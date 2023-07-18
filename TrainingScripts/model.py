import torch
import torch.nn as nn
from transformers.models.beit.modeling_beit import BeitUperHead, BeitEncoder, BeitLayer, BeitModelOutputWithPooling, BeitEmbeddings, BeitConfig
from transformers.modeling_outputs import BaseModelOutput
from einops import rearrange
from torch import einsum, nn
import torch.nn.functional as F
from helper import SEP

class Model(nn.Module):
    def __init__(self, output_channels, num_heads, config) -> None:
        super().__init__()

        self.output_channels = output_channels
        self.num_frames = num_heads
        self.add_info_length = 5 
        
        self.patch_size = 16
        self.num_channels = 3
        self.hidden_size = 768
        self.image_size = (640, 640) 
        self.window = (self.image_size[0] // self.patch_size, self.image_size[1] // self.patch_size) if self.image_size is not None else None

        # BEIT + CROSS-ATTENTION LAYERS
        beit_model_config = BeitConfig.from_pretrained('microsoft/beit-base-finetuned-ade-640-640')
        beit_model_config.num_hidden_layers = 6

        self.beit_embeddings = BeitEmbeddings(beit_model_config)
        self.encoder = BeitEncoder(beit_model_config)
        
        dpr = [x.item() for x in torch.linspace(0, beit_model_config.drop_path_rate, beit_model_config.num_hidden_layers)]
        self.encoder.layer = nn.ModuleList([
            nn.ModuleList([
                BeitLayer(beit_model_config,
                    window_size=self.beit_embeddings.patch_embeddings.patch_shape if beit_model_config.use_relative_position_bias else None,
                    drop_path_rate=dpr[i],
                ),
                CrossAttention(dim=self.hidden_size, context_dim=self.hidden_size, dim_head=64, heads=12, norm_context=True, ff_mult=True)
            ]) for i in range(beit_model_config.num_hidden_layers)
        ])
        self.encoder.forward = self.forward_encoder       

        # EMBEDDING SIMULATION PARAMETERS
        self.origin_embedding = nn.Embedding(8, self.hidden_size) 
        self.destination_embedding = nn.Embedding(2, self.hidden_size) 
        self.num_agents_embedding = nn.Embedding(3, self.hidden_size) 
        self.fp_size_embedding = nn.Linear(2, self.hidden_size)
        self.vel_embedding = nn.Embedding(3, self.hidden_size) 
        self.input_emb_scale = 8

        self.input_embedding = nn.Linear(self.add_info_length * self.hidden_size, self.add_info_length * self.hidden_size)
        self.evac_preprocess = nn.Linear(self.add_info_length * self.hidden_size,self.add_info_length * self.hidden_size) 
        

        self.num_hidden_ca_layers = 3 # 1 or 6 also work
        self.marriage_att = nn.ModuleList([
            CrossAttention(dim=self.hidden_size, context_dim=self.hidden_size, dim_head=64, heads=12, norm_context=True, ff_mult=True) for i in range(self.num_hidden_ca_layers)
        ])

        # FPN
        self.out_indices = [3, 5, 7, 11]
        self.fpn1 = nn.Sequential(
            nn.ConvTranspose2d(self.hidden_size, self.hidden_size, kernel_size=2, stride=2),
            nn.BatchNorm2d(self.hidden_size),
            nn.GELU(),
            nn.ConvTranspose2d(self.hidden_size, self.hidden_size, kernel_size=2, stride=2),
        )
        self.fpn2 = nn.Sequential(
            nn.ConvTranspose2d(self.hidden_size, self.hidden_size, kernel_size=2, stride=2),
        )
        self.fpn3 = nn.Identity()
        self.fpn4 = nn.MaxPool2d(kernel_size=2, stride=2)

        self.decode_head = BeitUperHead(beit_model_config)
        self.decode_head.classifier = ClassMovieClassifier(self.hidden_size, self.output_channels, self.num_frames)

        # EVACUATION PREDICTION
        self.evac_predictor = nn.Linear(self.add_info_length * self.hidden_size, 1)


    def forward(self, pixel_values: torch.Tensor, add_info = None) -> torch.Tensor:
        batch_size, num_channels, height, width = pixel_values.shape
        assert height % self.patch_size == 0 and width % self.patch_size == 0, 'Image size not patchable!'


        # EMBED SIMULATION INFORMATION
        num_origins_id = add_info[0]-1
        num_destinations_id = add_info[1]-1
        num_agents_id= add_info[2]
        fp_size = add_info[3]
        velocity_id = add_info[4]

        or_emb = self.origin_embedding(num_origins_id)
        dest_emb = self.destination_embedding(num_destinations_id)
        num_ag_emb = self.num_agents_embedding(num_agents_id)
        fp_size_emb = self.fp_size_embedding(fp_size)
        vel_emb = self.vel_embedding(velocity_id)

        info_emb = torch.cat((or_emb, dest_emb, num_ag_emb, fp_size_emb, vel_emb), dim=-1)
        info_emb = self.input_embedding(info_emb).view(batch_size, self.add_info_length, self.hidden_size)
        

        # EMBED IMAGE INFORMATION + CROSS ATTENTION
        embedding_output = self.beit_embeddings(pixel_values, None)

        encoder_outputs = self.encoder(
            embedding_output,
            info_emb,
            bool_masked_pos = None,
            head_mask = None,
            output_attentions = None,
            output_hidden_states = True,
            return_dict = True,
        )
        sequence_output = encoder_outputs[0]

        beit_model_output = BeitModelOutputWithPooling(
            last_hidden_state=sequence_output,
            pooler_output=None,
            hidden_states=encoder_outputs.hidden_states,
            attentions=encoder_outputs.attentions,
        )

        hidden_states = beit_model_output.last_hidden_state
        all_hidden_states = beit_model_output.hidden_states


        # FPN --> CLASSIFICATION
        features = [feature for idx, feature in enumerate(all_hidden_states) if idx + 1 in self.out_indices]
        batch_size = hidden_states.size()[0]
        patch_resolution_h, patch_resolution_w = height // self.patch_size, width // self.patch_size
        # reshape hidden states
        features = [
            x[:,1:,:].permute(0, 2, 1).reshape(batch_size, -1, patch_resolution_h, patch_resolution_w) for x in features
        ]
        
        ops = [self.fpn1, self.fpn2, self.fpn3, self.fpn4]
        for i in range(len(features)):
            features[i] = ops[i](features[i])

        logits = self.decode_head(features)
        logits = torch.stack(logits, dim=2).squeeze()

             
        # EVACUATION TIME PREDICTION
        info_emb_2 = torch.cat((or_emb, dest_emb, num_ag_emb, fp_size_emb, vel_emb), dim=-1)
        info_emb_2 = self.evac_preprocess(info_emb_2)

        for marr_layer in self.marriage_att:
            info_emb = marr_layer(info_emb, hidden_states) 

        info_emb = info_emb.flatten(start_dim=1)
        info_emb = info_emb + info_emb_2
        evac_prediction = self.evac_predictor(info_emb)


        return logits, evac_prediction


    def forward_encoder(
        self,
        hidden_states,
        vector_embeddings,
        bool_masked_pos = None,
        head_mask = None,
        output_attentions = False,
        output_hidden_states = True,
        return_dict = True,
    ):
        all_hidden_states = () if output_hidden_states else None
        all_self_attentions = () if output_attentions else None

        for i, layer_modules in enumerate(self.encoder.layer):
            if output_hidden_states:
                all_hidden_states = all_hidden_states + (hidden_states,)

            beit_layer = layer_modules[0]
            ca_layer = layer_modules[1]

            layer_outputs = beit_layer(hidden_states, None, output_attentions, None)
            layer_outputs = (ca_layer(layer_outputs[0], vector_embeddings), )

            hidden_states = layer_outputs[0]

            if output_attentions:
                all_self_attentions = all_self_attentions + (layer_outputs[1],)

        if output_hidden_states:
            all_hidden_states = all_hidden_states + (hidden_states,)

        if not return_dict:
            return tuple(v for v in [hidden_states, all_hidden_states, all_self_attentions] if v is not None)
        return BaseModelOutput(
            last_hidden_state=hidden_states,
            hidden_states=all_hidden_states,
            attentions=all_self_attentions,
        )


class CrossAttention(nn.Module):
    def __init__(
        self,
        dim,
        context_dim=None,
        dim_head=64,
        heads=8,
        parallel_ff=False,
        ff_mult=4,
        norm_context=False
    ):
        super().__init__()
        self.heads = heads
        self.scale = dim_head ** -0.5
        inner_dim = heads * dim_head

        def default(val, d):
            def exists(val):
                return val is not None
            return val if exists(val) else d
        
        context_dim = default(context_dim, dim)

        self.norm = nn.LayerNorm(dim)
        self.context_norm = nn.LayerNorm(context_dim) if norm_context else nn.Identity()

        self.to_q = nn.Linear(dim, inner_dim, bias=False)
        self.to_kv = nn.Linear(context_dim, dim_head * 2, bias=False)
        self.to_out = nn.Linear(inner_dim, dim, bias=False)

        # whether to have parallel feedforward

        ff_inner_dim = ff_mult * dim

        self.ff = nn.Sequential(
            nn.Linear(dim, ff_inner_dim * 2, bias=False),
            SwiGLU(),
            nn.Linear(ff_inner_dim, dim, bias=False)
        ) if parallel_ff else None


    def forward(self, x, context):

        x = self.norm(x)
        context = self.context_norm(context)

        # queries, keys and values
        q = self.to_q(x)
        q = rearrange(q, 'b n (h d) -> b h n d', h = self.heads)

        q = q * self.scale

        k, v = self.to_kv(context).chunk(2, dim=-1)

        sim = einsum('b h i d, b j d -> b h i j', q, k)

        # attention
        sim = sim - sim.amax(dim=-1, keepdim=True)
        attn = sim.softmax(dim=-1)

        out = einsum('b h i j, b j d -> b h i d', attn, v)

        out = rearrange(out, 'b h n d -> b n (h d)')
        out = self.to_out(out)

        if self.ff:
            out = out + self.ff(x)

        return out


class SwiGLU(nn.Module):
    def forward(self, x):
        x, gate = x.chunk(2, dim=-1)
        return F.silu(gate) * x


class ClassMovieClassifier(nn.Module):
    def __init__(self, input_channels, output_channels, num_frames) -> None:
        super().__init__()

        self.module_list = nn.ModuleList([
            nn.Sequential(
                nn.Conv2d(input_channels, output_channels, kernel_size=1),
                nn.BatchNorm2d(output_channels),
                nn.ReLU()
            ) for i in range(num_frames)
        ])

        self.apply(self._initialize_weights)
    
    def _initialize_weights(self, m):
        if hasattr(m, 'weight') or hasattr(m, 'bias'):
            try:
                torch.nn.init.xavier_normal_(m.weight)
            except ValueError:
                # Prevent ValueError("Fan in and fan out can not be computed for tensor with fewer than 2 dimensions")
                m.weight.data.uniform_(-0.2, 0.2)
            if m.bias is not None:
                m.bias.data.zero_()

    def forward(self, input):
        return [module(input) for module in self.module_list]
