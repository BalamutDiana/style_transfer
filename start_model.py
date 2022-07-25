from PIL import Image
from torchvision.utils import save_image
from classes import *

import torchvision.transforms as transforms
import torchvision.models as models
import torch.optim as optim

import copy

def image_loader(image_name, imsize = 480):

    loader = transforms.Compose([
        transforms.Resize(imsize),  # нормируем размер изображения
        transforms.CenterCrop(imsize),
        transforms.ToTensor()])  # превращаем в удобный форма

    image = Image.open(image_name)
    image = loader(image).unsqueeze(0)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    return image.to(device, torch.float)

def get_style_model_and_losses(cnn, normalization_mean, normalization_std,
                               style_img, content_img):

    content_layers = ['conv_4']
    style_layers = ['conv_1', 'conv_2', 'conv_3', 'conv_4', 'conv_5']
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    cnn = copy.deepcopy(cnn)
    normalization = Normalization(normalization_mean, normalization_std).to(device)
    content_losses = []
    style_losses = []

    model = nn.Sequential(normalization)

    i = 0  # increment every time we see a conv
    for layer in cnn.children():
        if isinstance(layer, nn.Conv2d):
            i += 1
            name = 'conv_{}'.format(i)
        elif isinstance(layer, nn.ReLU):
            name = 'relu_{}'.format(i)
            layer = nn.ReLU(inplace=False)
        elif isinstance(layer, nn.MaxPool2d):
            name = 'pool_{}'.format(i)
        elif isinstance(layer, nn.BatchNorm2d):
            name = 'bn_{}'.format(i)
        else:
            raise RuntimeError('Unrecognized layer: {}'.format(layer.__class__.__name__))

        model.add_module(name, layer)

        if name in content_layers:
            # add content loss:
            target = model(content_img).detach()
            content_loss = ContentLoss(target)
            model.add_module("content_loss_{}".format(i), content_loss)
            content_losses.append(content_loss)

        if name in style_layers:
            # add style loss:
            target_feature = model(style_img).detach()
            style_loss = StyleLoss(target_feature)
            model.add_module("style_loss_{}".format(i), style_loss)
            style_losses.append(style_loss)

    for i in range(len(model) - 1, -1, -1):
        if isinstance(model[i], ContentLoss) or isinstance(model[i], StyleLoss):
            break

    model = model[:(i + 1)]

    return model, style_losses, content_losses

def get_input_optimizer(input_img):
    optimizer = optim.LBFGS([input_img.requires_grad_()])
    #optimizer =  torch.optim.Adam([input_img.requires_grad_()], lr=5e-3)
    return optimizer

def run_style_transfer(cnn, content_img, style_img, input_img, num_steps=300,
                       style_weight=100000, content_weight=1):
    print('Building the style transfer model..')

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    normalization_mean = torch.tensor([0.485, 0.456, 0.406]).to(device)
    normalization_std = torch.tensor([0.229, 0.224, 0.225]).to(device)

    model, style_losses, content_losses = get_style_model_and_losses(cnn,
                                                                     normalization_mean, normalization_std,
                                                                     style_img, content_img)
    optimizer = get_input_optimizer(input_img)

    print('Optimizing..')
    run = [0]
    while run[0] <= num_steps:

        def closure():
            # correct the values
            # это для того, чтобы значения тензора картинки не выходили за пределы [0;1]
            input_img.data.clamp_(0, 1)

            optimizer.zero_grad()

            model(input_img)

            style_score = 0
            content_score = 0

            for sl in style_losses:
                style_score += sl.loss
            for cl in content_losses:
                content_score += cl.loss

            # взвешивание ощибки
            style_score *= style_weight
            content_score *= content_weight

            loss = style_score + content_score
            loss.backward()

            run[0] += 1
            if run[0] % 50 == 0:
                print("run {}:".format(run))
                print('Style Loss : {:4f} Content Loss: {:4f}'.format(
                    style_score.item(), content_score.item()))
                print()

            return style_score + content_score

        optimizer.step(closure)

    # a last correction...
    input_img.data.clamp_(0, 1)

    return input_img

async def style_start(style_name = "style.jpg"):
    style_img = image_loader(style_name)
    content_img = image_loader("content.jpg")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    cnn = models.vgg19(pretrained=True).features.to(device).eval()

    input_img = content_img.clone()

    output = run_style_transfer(cnn, content_img, style_img, input_img)

    save_image(output, 'result.jpg')

