import torch
from torch.nn import functional as F
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.optim import Adam
import pytorch_lightning as pl
from model import Model
from helper import SEP

class ImageModule(pl.LightningModule):
    def __init__(
        self, 
        config: dict,
        train_config: dict,
        ):
        super(ImageModule, self).__init__()

        self.config = config
        
        self.learning_rate = train_config['learning_rate']
        self.lr_sch_factor = train_config['lr_sch_factor']
        self.lr_sch_patience = train_config['lr_sch_patience']

        self.init = train_config['init'] if train_config['init'] is not None else 'xavier'

        self.num_heads = 1

        self.train_losses = {}
        self.train_losses_per_epoch = {}
        self.val_losses = {}
        self.val_losses_per_epoch = {}
        self.loss_func_params = train_config['loss_dict']
        self.alpha = self.loss_func_params['alpha']
        self.beta = self.loss_func_params['beta']

        self.img_loss_factor = 50.
        self.output_channels = 4
        self.num_heads = 8
        
        self.log_result = {'validation': [], 'training': []}
        self.model = Model(self.output_channels, self.num_heads, config=config)
        
        self.model.apply(self._initialize_weights)


    def _initialize_weights(self, m):
        if hasattr(m, 'weight'):
            try:
                if self.init == 'xavier':
                    torch.nn.init.xavier_normal_(m.weight)
                elif self.init == 'normal':
                    torch.nn.init.normal_(m.weight, mean=0, std=0.1)
                elif self.init == 'uniform':
                    m.weight.data.uniform_(-0.1, 0.1)
            except ValueError:
                m.weight.data.uniform_(-0.2, 0.2)
        elif hasattr(m, 'bias'):
            m.bias.data.zero_()


    def tversky_loss(self, gt, logits, eps=1e-7):
        true_1_hot = torch.eye(self.output_channels)[gt.unsqueeze(1).squeeze(1)] 
        true_1_hot = true_1_hot.permute(0, 4, 1, 2, 3).float()
        probas = F.softmax(logits, dim=1)

        true_1_hot = true_1_hot.type(logits.type())
        intersection = torch.sum(probas * true_1_hot, (0, 2, 3, 4))
        fps = torch.sum(probas * (1 - true_1_hot), (0, 2, 3, 4))
        fns = torch.sum((1 - probas) * true_1_hot, (0, 2, 3, 4))
        num = intersection
        denom = intersection + (self.alpha * fps) + (self.beta * fns)
        tversky_loss = (num / (denom + eps)).mean()
        return (1 - tversky_loss)


    def forward(self, x, *args):
        return self.model(x, *args)

    def training_step(self, batch, batch_idx: int):
        img, traj, add_info = batch

        traj, evac_time = traj
        traj_pred, evac_time_pred = traj_pred, evac_time_pred = self.forward(img, add_info)

        img_loss = self.tversky_loss(traj, traj_pred)
        evac_loss = F.mse_loss(evac_time_pred.squeeze(), evac_time.float())

        train_loss = img_loss * self.img_loss_factor + evac_loss

        evac_l1_loss = F.l1_loss(evac_time_pred.clone().detach().squeeze(), evac_time.clone().detach())

        self.internal_log({'img_loss': img_loss, 'evac_loss': evac_loss, 'evac_L1': evac_l1_loss}, stage='train')

        self.log('loss', train_loss, on_step=False, on_epoch=True, prog_bar=True, logger=False)
        return {'loss' : train_loss}


    def validation_step(self, batch, batch_idx: int) -> None:
        img, traj, add_info = batch

        traj, evac_time = traj
        traj_pred, evac_time_pred = self.forward(img, add_info)

        img_loss = self.tversky_loss(traj, traj_pred)
        evac_loss = F.mse_loss(evac_time_pred.squeeze(), evac_time.float())

        val_loss = img_loss * self.img_loss_factor + evac_loss

        evac_l1_loss = F.l1_loss(evac_time_pred.clone().detach().squeeze(), evac_time.clone().detach())

        self.internal_log({'img_loss': img_loss, 'evac_loss': evac_loss, 'evac_L1': evac_l1_loss}, stage='val')

        self.log('val_loss', val_loss, on_step=False, on_epoch=True, prog_bar=True, logger=False)
        return {'val_loss' : val_loss}


    def internal_log(self, losses_it, stage):
        if self.trainer.state.stage == 'sanity_check': return

        losses_logger = self.train_losses if stage=='train' else self.val_losses

        for key, val in losses_it.items():
            if key not in losses_logger:
                losses_logger.update({key: [val]})
            else:
                losses_logger[key].append(val)


    def configure_optimizers(self):
        optimizer = Adam(self.model.parameters(), lr = self.learning_rate)
        return {
            'optimizer': optimizer,
            'lr_scheduler': ReduceLROnPlateau(optimizer, factor=self.lr_sch_factor, patience=self.lr_sch_patience),
            'monitor': 'val_loss'
            }


    def on_train_epoch_start(self) -> None:        

        if self.trainer.state.stage in ['sanity_check']: return super().on_train_epoch_start()
        
        if self.current_epoch > 0: 
            self.print_logs()
    

    def print_logs(self):
        # Training Logs
        for key, val in self.train_losses.items():
            if key not in self.train_losses_per_epoch:
                mean = torch.as_tensor(val).nanmean()
                self.train_losses_per_epoch.update({key: [mean.item()]})
            else:
                self.train_losses_per_epoch[key].append(torch.as_tensor(val).nanmean().item())

        # Validation logs
        for key, val in self.val_losses.items():
            if key not in self.val_losses_per_epoch:
                mean = torch.as_tensor(val).nanmean()
                self.val_losses_per_epoch.update({key: [mean.item()]})
            else:
                self.val_losses_per_epoch[key].append(torch.as_tensor(val).nanmean().item())

        # Reset
        self.train_losses = {}
        self.val_losses = {}
        
        print('\nTRAINING RESULT:')
        train_string = ''
        train_vals = [val for val in self.train_losses_per_epoch.values()]
        for id_k, key in enumerate(list(self.train_losses_per_epoch.keys())):
            if id_k == 0:
                train_string += key+':'
            else:
                train_string += '\t\t' + key+':'
        for i_epoch in range(len(train_vals[0])):
            for i_loss in range(len(train_vals)):
                if i_loss == 0:
                    train_string += f'\n{train_vals[i_loss][i_epoch]:.5f}'
                else:
                    train_string += f'\t\t\t{train_vals[i_loss][i_epoch]:.5f}'
        print(train_string) 


        print('\nVALIDATION RESULT:')
        val_string = ''
        val_vals = [val for val in self.val_losses_per_epoch.values()]
        for id_k, key in enumerate(list(self.val_losses_per_epoch.keys())):
            if id_k == 0:
                val_string += key+':'
            else:
                val_string += '\t\t' + key+':'
        for i_epoch in range(len(val_vals[0])):
            for i_loss in range(len(val_vals)):
                if i_loss == 0:
                    val_string += f'\n{val_vals[i_loss][i_epoch]:.5f}'
                else:
                    val_string += f'\t\t\t{val_vals[i_loss][i_epoch]:.5f}'
        print(val_string) 
        
