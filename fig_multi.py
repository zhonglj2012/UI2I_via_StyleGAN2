import os
import argparse
import math
import pdb

import torch
from torch import optim
from torch.nn import functional as F
from torchvision import transforms
from PIL import Image
from tqdm import tqdm
from utils import AddPepperNoise
import numpy as np
from scipy.linalg import solve

import lpips
from model import Generator
import random
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--model1", type=str, required=True)
parser.add_argument("--model2", type=str, required=True)
# parser.add_argument("--model3", type=str, required=True)
parser.add_argument("--size1", type=int, default=1024)
parser.add_argument("--size2", type=int, default=1024)
# parser.add_argument("--size3", type=int, default=1024)
parser.add_argument("-o", "--output", type=str, required=True)
parser.add_argument("--device", type=str, default="cuda")
parser.add_argument('--truncation_mean', type=int, default=4096)
parser.add_argument("-r", "--randnum", type=int, default=10)
#parser.add_argument("factor_face", type=str)
#parser.add_argument("factor_metface", type=str)

args = parser.parse_args()

#torch.manual_seed(8009268845030607599)
#seed = random.randrange(sys.maxsize)
seed=8009268845030607599
torch.manual_seed(seed)
print("Seed was:", seed)

def noise_normalize_(noises):
    for noise in noises:
        mean = noise.mean()
        std = noise.std()

        noise.data.add_(-mean).div_(std)

def make_image(tensor):
    return (
        tensor.detach()
        .clamp_(min=-1, max=1)
        .add(1)
        .div_(2)
        .mul(255)
        .type(torch.uint8)
        .permute(0, 2, 3, 1)
        .to("cpu")
        .numpy()
    )

device = args.device

# generate images
## load model
g_ema1 = Generator(args.size1, 512, 8)
g_ema1.load_state_dict(torch.load(args.model1, map_location='cuda:0')["g_ema"], strict=False)
g_ema1.eval()
g_ema1 = g_ema1.to(device)

g_ema2 = Generator(args.size2, 512, 8)
g_ema2.load_state_dict(torch.load(args.model2, map_location='cuda:0')["g_ema"], strict=False)
g_ema2.eval()
g_ema2 = g_ema2.to(device)

# g_ema3 = Generator(args.size3, 512, 8)
# g_ema3.load_state_dict(torch.load(args.model3, map_location='cuda:0')["g_ema"], strict=False)
# #g_ema3.style = g_ema1.style
# g_ema3.eval()
# g_ema3 = g_ema3.to(device)

## prepare input vector
sample_z = torch.randn(1, 512, device=args.device)
sample_z_style = torch.randn(1, 512, device=args.device)

## noise
noises_single = g_ema2.make_noise()
noises = []
for noise in noises_single:
    noises.append(noise.repeat(1, 1, 1, 1).normal_())
noise_normalize_(noises)

## gen images
with torch.no_grad():
    #mean_latent1 = g_ema1.mean_latent(args.truncation_mean)
    mean_latent1 = g_ema2.mean_latent(args.truncation_mean)
    mean_latent2 = g_ema2.mean_latent(args.truncation_mean)
    #mean_latent2 = g_ema1.mean_latent(args.truncation_mean)

img1, swap_res = g_ema1([sample_z], truncation=1, truncation_latent=mean_latent1, save_for_swap=True)
img1_name = args.output + str(seed) + "_a.png"
img1 = make_image(img1)
out1 = Image.fromarray(img1[0])
out1.save(img1_name)

# img2, _ = g_ema2([sample_z], truncation=0.5, truncation_latent=mean_latent2, swap=True, swap_tensor=swap_res)
# img2_name = args.output + "_fcftls.png"
# img2 = make_image(img2)
# out2 = Image.fromarray(img2[0])
# out2.save(img2_name)
#
# img3, _ = g_ema2([sample_z], truncation=0.5, truncation_latent=mean_latent2)
# img3_name = args.output + "_fcft.png"
# img3 = make_image(img3)
# out3 = Image.fromarray(img3[0])
# out3.save(img3_name)
#
# img4, _ = g_ema3([sample_z], truncation=0.5, truncation_latent=mean_latent2)
# img4_name = args.output + "_ft.png"
# img4 = make_image(img4)
# out4 = Image.fromarray(img4[0])
# out4.save(img4_name)
#
# img5, _ = g_ema3([sample_z], truncation=0.5, truncation_latent=mean_latent2, swap=True, swap_tensor=swap_res)
# img5_name = args.output + "_ftls.png"
# img5 = make_image(img5)
# out5 = Image.fromarray(img5[0])
# out5.save(img5_name)
for i in range(20):
    sample_z_style = torch.randn(1, 512, device=args.device)
    img4, _ = g_ema2([sample_z], truncation=0.5, truncation_latent=mean_latent2, swap=True, swap_tensor=swap_res, multi_style=True, multi_style_latent=[sample_z_style])
    #img4, _ = g_ema2([sample_z], truncation=0.5, truncation_latent=mean_latent2, swap=False, multi_style=True, multi_style_latent=[sample_z_style])
    print(i)
    img4_name = args.output + str(seed) + "_" + str(i) + ".png"
    img4 = make_image(img4)
    out4 = Image.fromarray(img4[0])
    out4.save(img4_name)