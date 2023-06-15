import torch
import torch.nn as nn
from transformers.models.beit.modeling_beit import BeitEncoder, BeitLayer, BeitModelOutputWithPooling, BeitEmbeddings, BeitRelativePositionBias, BeitConfig
from transformers.activations import ACT2FN
from transformers.modeling_outputs import BaseModelOutput
import math
from einops import rearrange, repeat
from torch import einsum, nn
import torch.nn.functional as F

class MyModel(nn.Module):
    def __init__(self, mode, output_channels, num_heads, additional_info, config) -> None:
        super().__init__()

        assert mode in ['denseClass_wEvac', 'density_class']
        # assert additional_info == True
        self.mode = mode
        self.additional_info = additional_info

        # Sequence? TF or visual TF
        # TODO last layer --> BN,  so far 68472 samples, with corr_edge it is 130356
        # --[CHECK]-- positional embedding yes/no? if yes, self.position_embeddings + emb or like CoCa?
        # --[CHECK]-- attention pooling for image tokens (CoCa)
        # loss functions (wCE vs Tversky)
        # img reading (padded vs raw)
        # network: self.attention_key/val/qu  VS.  q, k, v, ff = self.fused_attn_ff_proj(x).split(self.fused_dims, dim=-1) (CoCa)
        # --[CHECK]-- marriage: how (cross attention vs concatenation) and where (before/after)

        # contrastive loss?
        self.decoder_mode = config['decoder_mode']
        self.settings = config['settings']
        self.output_channels = output_channels
        self.num_frames = num_heads
        self.add_info_length = 5 
        self.final_conv_batch = self.settings['final_conv_batch'] if 'final_conv_batch' in self.settings else False

        self.output_hidden_states = False
        self.marriage_mode = self.settings['marriage_mode'] # 0=before, 1=during, 2=after
        if self.marriage_mode == 1: raise NotImplementedError('During attention requires as many CrossAttention layers as TF layers')
        
        # EMBEDDING IMAGE
        self.patch_size = 16
        self.num_channels = 3
        self.hidden_size = self.settings['hidden_size'] # 768 as default

        self.image_size = (640, 640) # None
        self.window = (self.image_size[0] // self.patch_size, self.image_size[1] // self.patch_size) if self.image_size is not None else None

        # BEIT LAYERS
        # beit_model_config = BeitForSemanticSegmentation.from_pretrained('microsoft/beit-base-finetuned-ade-640-640').config
        from transformers.models.beit.modeling_beit import BeitConfig
        beit_model_config = BeitConfig.from_pretrained('microsoft/beit-base-finetuned-ade-640-640')
        beit_model_config.num_hidden_layers = config['num_hidden_img_layers']
        """config_pretrained = beit_model.config
        config_pretrained.hidden_size = self.hidden_size
        config_pretrained.use_mask_token = False
        config_pretrained.use_absolute_position_embeddings = False
        config_pretrained.hidden_dropout_prob = 0.0
        config_pretrained.image_size = 640
        config_pretrained.patch_size = 16
        config_pretrained.num_channels = 3
        config_pretrained.layer_norm_eps = 1e-12
        config_pretrained.use_mean_pooling = True
        config_pretrained.use_shared_relative_position_bias = True """
        # self.beit = BeitModel(beit_model_config)

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
        if self.additional_info:
            # distr
            # assert (self.hidden_size / self.add_info_length).is_integer()
            # self.od_distances_embedding = nn.Linear(16, self.hidden_size) # //self.add_info_length)
            self.origin_embedding = nn.Embedding(8, self.hidden_size) # nn.Linear(1, self.hidden_size) 
            self.destination_embedding = nn.Embedding(2, self.hidden_size) # nn.Linear(1, self.hidden_size)
            self.num_agents_embedding = nn.Embedding(3, self.hidden_size) # nn.Linear(1, self.hidden_size)
            self.fp_size_embedding = nn.Linear(2, self.hidden_size)
            self.vel_embedding = nn.Embedding(3, self.hidden_size) # nn.Linear(1, self.hidden_size)
            self.input_emb_scale = 8

            self.input_embedding = nn.Linear(self.add_info_length * self.hidden_size, self.add_info_length * self.hidden_size)
            # self.input_embedding = nn.Linear(self.add_info_length * self.hidden_size, self.input_emb_scale * self.hidden_size)
        if mode=='denseClass_wEvac':
            self.evac_preprocess = nn.Linear(self.add_info_length * self.hidden_size,self.add_info_length * self.hidden_size) 
            self.evac_predictor = nn.Linear(self.add_info_length * self.hidden_size, 1)

            # several layers?
            self.num_hidden_ca_layers = self.settings['num_hidden_ca_layers']
            # self.marriage_att = CrossAttention(dim=self.hidden_size, context_dim=self.hidden_size, dim_head=64, heads=12, norm_context=True, ff_mult=True)
            self.marriage_att = nn.ModuleList([
                CrossAttention(dim=self.hidden_size, context_dim=self.hidden_size, dim_head=64, heads=12, norm_context=True, ff_mult=True) for i in range(self.num_hidden_ca_layers)
            ])
            # also cross attention here?


        if self.settings['use_pe']:
            # self.positional_embedding = nn.Parameter(torch.zeros(1, num_patches + 1, config.hidden_size))
            max_len = 10000
            self.positional_encoding = torch.zeros(max_len, self.hidden_size)
            position = torch.arange(0, max_len).unsqueeze(1).float()
            div_term = torch.exp(torch.arange(0, self.hidden_size, 2).float() * -(math.log(10000.0) / self.hidden_size))
            self.positional_encoding[:, 0::2] = torch.sin(position * div_term)
            self.positional_encoding[:, 1::2] = torch.cos(position * div_term)
            self.positional_encoding = self.positional_encoding.unsqueeze(0)

        if self.settings['attn_pooling']:
            # attention pooling for image tokens
            self.img_queries = nn.Parameter(torch.randn(self.hidden_size, self.hidden_size)) # 256, self.hidden_size))
            self.img_attn_pool = CrossAttention(dim=self.hidden_size, context_dim=self.hidden_size, dim_head=64, heads=12, norm_context=True)
            self.img_attn_pool_norm = nn.LayerNorm(self.hidden_size)
            

        # HOW TO DECODE FROM hidden_states
        if self.decoder_mode == 'fpn':
            from transformers.models.beit.modeling_beit import BeitUperHead, BeitConfig
            self.output_hidden_states = True
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

            # Semantic segmentation head(s)           
            self.decode_head = BeitUperHead(beit_model_config)
            self.decode_head.classifier = ClassMovieClassifier(self.hidden_size, self.output_channels, self.num_frames, self.final_conv_batch)
            # nn.ModuleList(
            #     [nn.Sequential(
            #         nn.Conv2d(self.hidden_size, self.output_channels, kernel_size=1), 
            #         nn.ReLU()) for i in range(self.num_frames)]
            # )

        elif self.decoder_mode == 'trans_conv':
            self.tc1 = nn.Sequential(
                nn.ConvTranspose2d(self.hidden_size, self.hidden_size, kernel_size=2, stride=2),
                nn.BatchNorm2d(self.hidden_size),
                nn.GELU(),
                nn.ConvTranspose2d(self.hidden_size, self.hidden_size, kernel_size=2, stride=2),
            )
            self.tc2 = nn.Sequential(
                nn.ConvTranspose2d(self.hidden_size, self.hidden_size, kernel_size=2, stride=2),
            )
            self.tc3 = nn.MaxPool2d(kernel_size=2, stride=2)

            self.decode_head = ClassMovieClassifier(self.hidden_size, self.output_channels, self.num_frames, self.final_conv_batch) 

        self.apply(self._initialize_weights)

    
    def _initialize_weights(self, m):
        if hasattr(m, 'weight'):
            try:
                torch.nn.init.xavier_normal_(m.weight)
                # torch.nn.init.normal_(m.weight, mean=0, std=0.1)
                # m.weight.data.uniform_(-0.1, 0.1)
            except ValueError:
                # Prevent ValueError("Fan in and fan out can not be computed for tensor with fewer than 2 dimensions")
                m.weight.data.uniform_(-0.2, 0.2)
                # print("Bypassing ValueError...")
        elif hasattr(m, 'bias'):
            m.bias.data.zero_()


    def forward(self, pixel_values: torch.Tensor, add_info = None) -> torch.Tensor:
        batch_size, num_channels, height, width = pixel_values.shape
        assert height % self.patch_size == 0 and width % self.patch_size == 0, 'Image size not patchable!'

        if add_info is not None:
            # distances = add_info[0]
            num_origins_id = add_info[0]-1
            num_destinations_id = add_info[1]-1
            num_agents_id= add_info[2]
            fp_size = add_info[3]
            velocity_id = add_info[4]

            if fp_size.ndim == 1:
                fp_size = fp_size.unsqueeze(0)

            or_emb = self.origin_embedding(num_origins_id)
            dest_emb = self.destination_embedding(num_destinations_id)
            num_ag_emb = self.num_agents_embedding(num_agents_id)
            fp_size_emb = self.fp_size_embedding(fp_size)
            vel_emb = self.vel_embedding(velocity_id)

            info_emb = torch.cat((or_emb, dest_emb, num_ag_emb, fp_size_emb, vel_emb), dim=-1)
            info_emb = self.input_embedding(info_emb).view(batch_size, self.add_info_length, self.hidden_size)

        # if self.settings['use_pe']:
        #     add_me = self.positional_encoding[:, :hidden_states.size(1), :].repeat(batch_size, 1, 1).to(hidden_states.device)
        #     hidden_states = hidden_states + add_me
        
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
        
        if self.settings['attn_pooling']:
            img_queries = repeat(self.img_queries, 'n d -> b n d', b=hidden_states.shape[0])
            img_queries = self.img_attn_pool(img_queries, hidden_states)
            img_queries = self.img_attn_pool_norm(img_queries)
    
        # patch_resolution * 4
        if self.decoder_mode == 'fpn':
            # FPNs: input: (640, 640), hidden_states: (2, 1600, 768) --> (2, 5, 160, 160)  //  input: (768, 256), hidden_states: (2, 768, 768) --> (2, 5, 192, 64)
            features = [feature for idx, feature in enumerate(all_hidden_states) if idx + 1 in self.out_indices]
            batch_size = hidden_states.size()[0] # pixel_values.shape[0]
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

        # patch_resolution * 4
        elif self.decoder_mode == 'trans_conv':
            patch_resolution_h, patch_resolution_w = height // self.patch_size, width // self.patch_size
            features = hidden_states.permute(0, 2, 1).reshape(batch_size, -1, patch_resolution_h, patch_resolution_w)

            for tc in [self.tc1, self.tc2, self.tc3]:
                features = tc(features)
            
            logits = self.decode_head(features)
            logits = torch.stack(logits, dim=2).squeeze()

             
        # MARRIAGE AFTER
        if self.mode=='denseClass_wEvac' and add_info is not None:
            info_emb_2 = torch.cat((or_emb, dest_emb, num_ag_emb, fp_size_emb, vel_emb), dim=-1)
            info_emb_2 = self.evac_preprocess(info_emb_2)

            # info_emb = self.marriage_att(info_emb, img_queries) if self.settings['attn_pooling'] else self.marriage_att(info_emb, hidden_states)
            for marr_layer in self.marriage_att:
                info_emb = marr_layer(info_emb, hidden_states) # if self.settings['attn_pooling'] else marr_layer(info_emb, hidden_states)

            info_emb = info_emb.flatten(start_dim=1)
            info_emb = info_emb + info_emb_2
            evac_prediction = self.evac_predictor(info_emb)
            evac_prediction = nn.ReLU()(evac_prediction) # + upper theshold ReLU()?
            evac_prediction = torch.multiply(evac_prediction, 100.)

            return logits, evac_prediction
        
        return logits
    

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
        # assuming relative_position_bias = None and gradient_checkpointing = False
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


class Layer(nn.Module):
    def __init__(self, drop_path_rate=0.0, num_attention_heads=12, hidden_size=768, window=None) -> None:
        super().__init__()
        self.intermediate_size = 3072
        self.dropout_rate = drop_path_rate
        self.layer_scale_init_value = 0.1
        self.window = window

        # BeitSelfAttention (BeitAttention)
        self.num_attention_heads = num_attention_heads
        self.hidden_size = hidden_size
        assert self.hidden_size % self.num_attention_heads == 0, f'The hidden size {self.hidden_size,} is not a multiple of num_attention_heads!'
        self.attention_head_size = int(self.hidden_size / self.num_attention_heads)
        self.all_head_size = self.num_attention_heads * self.attention_head_size

        self.attention_query = nn.Linear(self.hidden_size, self.all_head_size)
        self.attention_key = nn.Linear(self.hidden_size, self.all_head_size, bias=False)
        self.attention_value = nn.Linear(self.hidden_size, self.all_head_size)
        if self.window is not None:
            config_pretrained = BeitConfig()
            config_pretrained.num_attention_heads = self.num_attention_heads
            self.attention_rel_pos_bias = BeitRelativePositionBias(config_pretrained, window_size=self.window)

        # BeitSelfOutput (BeitAttention)
        self.attention_output = nn.Linear(self.hidden_size, self.hidden_size)

        # BeitIntermediate
        self.intermediate = nn.Linear(self.hidden_size, self.intermediate_size)
        self.intermediate_act_fn = ACT2FN['gelu']

        # BeitOutput
        self.output = nn.Linear(self.intermediate_size, self.hidden_size)

        self.layernorm_before = nn.LayerNorm(self.hidden_size, eps=1e-12)
        self.drop_path = BeitDropPath(self.dropout_rate) if self.dropout_rate > 0.0 else nn.Identity()
        self.layernorm_after = nn.LayerNorm(self.hidden_size, eps=1e-12)
        init_values = self.layer_scale_init_value
        if init_values > 0:
            self.lambda_1 = nn.Parameter(init_values * torch.ones((self.hidden_size)), requires_grad=True)
            self.lambda_2 = nn.Parameter(init_values * torch.ones((self.hidden_size)), requires_grad=True)

    
    def transpose_for_scores(self, x):
        new_x_shape = x.size()[:-1] + (self.num_attention_heads, self.attention_head_size)
        x = x.view(*new_x_shape)
        return x.permute(0, 2, 1, 3)

        
    def forward(self, hidden_states):

        mixed_query_layer = self.attention_query(self.layernorm_before(hidden_states))

        key_layer = self.transpose_for_scores(self.attention_key(hidden_states))
        value_layer = self.transpose_for_scores(self.attention_value(hidden_states))
        query_layer = self.transpose_for_scores(mixed_query_layer)

        # Take the dot product between "query" and "key" to get the raw attention scores.
        attention_scores = torch.matmul(query_layer, key_layer.transpose(-1, -2))
        attention_scores = attention_scores / math.sqrt(self.attention_head_size)

        # Add relative position bias if present.
        if self.window is not None:
            attention_scores = attention_scores + self.attention_rel_pos_bias()[:,1:,1:].unsqueeze(0) # cls token not included, thats why [:,1:,1:]

        # Normalize the attention scores to probabilities.
        attention_probs = nn.functional.softmax(attention_scores, dim=-1)

        context_layer = torch.matmul(attention_probs, value_layer)

        context_layer = context_layer.permute(0, 2, 1, 3).contiguous()
        new_context_layer_shape = context_layer.size()[:-2] + (self.all_head_size,)
        context_layer = context_layer.view(*new_context_layer_shape)

        attention_output = self.attention_output(context_layer)

        if self.lambda_1 is not None:
            attention_output = self.lambda_1 * attention_output
        
        # first residual connection
        hidden_states = self.drop_path(attention_output) + hidden_states

        layer_output = self.layernorm_after(hidden_states)

        layer_output = self.intermediate(layer_output)
        layer_output = self.output(layer_output)

        if self.lambda_2 is not None:
            layer_output = self.lambda_2 * layer_output

        # second residual connection
        outputs = self.drop_path(layer_output) + hidden_states

        return outputs


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
        """
        einstein notation
        b - batch
        h - heads
        n, i, j - sequence length (base sequence length, source, target)
        d - feature dimension
        """

        # pre-layernorm, for queries and context

        x = self.norm(x)
        context = self.context_norm(context)

        # get queries

        q = self.to_q(x)
        q = rearrange(q, 'b n (h d) -> b h n d', h = self.heads)

        # scale

        q = q * self.scale

        # get key / values

        k, v = self.to_kv(context).chunk(2, dim=-1)

        # query / key similarity

        sim = einsum('b h i d, b j d -> b h i j', q, k)

        # attention

        sim = sim - sim.amax(dim=-1, keepdim=True)
        attn = sim.softmax(dim=-1)

        # aggregate

        out = einsum('b h i j, b j d -> b h i d', attn, v)

        # merge and combine heads

        out = rearrange(out, 'b h n d -> b n (h d)')
        out = self.to_out(out)

        # add parallel feedforward (for multimodal layers)
        if self.ff:
            out = out + self.ff(x)

        return out


class BeitDropPath(nn.Module):
    """Drop paths (Stochastic Depth) per sample (when applied in main path of residual blocks)."""

    def __init__(self, drop_prob: float = None) -> None:
        super().__init__()
        self.drop_prob = drop_prob

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
            Drop paths (Stochastic Depth) per sample (when applied in main path of residual blocks).

            Comment by Ross Wightman: This is the same as the DropConnect impl I created for EfficientNet, etc networks,
            however, the original name is misleading as 'Drop Connect' is a different form of dropout in a separate paper...
            See discussion: https://github.com/tensorflow/tpu/issues/494#issuecomment-532968956 ... I've opted for changing the
            layer and argument names to 'drop path' rather than mix DropConnect as a layer name and use 'survival rate' as the
            argument.
        """

        if self.drop_prob == 0.0 or not self.training:
            return x
        keep_prob = 1 - self.drop_prob
        shape = (x.shape[0],) + (1,) * (x.ndim - 1)  # work with diff dim tensors, not just 2D ConvNets
        random_tensor = keep_prob + torch.rand(shape, dtype=x.dtype, device=x.device)
        random_tensor.floor_()  # binarize
        output = x.div(keep_prob) * random_tensor
        return output



class SwiGLU(nn.Module):
    def forward(self, x):
        x, gate = x.chunk(2, dim=-1)
        return F.silu(gate) * x


class ClassMovieClassifier(nn.Module):
    def __init__(self, input_channels, output_channels, num_frames, final_batch=False) -> None:
        super().__init__()

        if not final_batch:
            self.module_list = nn.ModuleList([
                nn.Sequential(
                    nn.Conv2d(input_channels, output_channels, kernel_size=1),
                    nn.ReLU()
                ) for i in range(num_frames)
            ])

        else:
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
                # print("Bypassing ValueError...")
            if m.bias is not None:
                m.bias.data.zero_()

    def forward(self, input):
        return [module(input) for module in self.module_list]
