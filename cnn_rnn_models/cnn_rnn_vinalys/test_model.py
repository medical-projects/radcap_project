import torch
import matplotlib.pyplot as plt
import numpy as np
import argparse
import pickle
import os
import json
from torchvision import transforms
from build_vocab import Vocabulary
from model_cnn_rnn import EncoderCNN, DecoderRNN
from PIL import Image

# Device configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


def load_image(image_path, transform=None):
    image = Image.open(image_path).convert('RGB')
    image = image.resize([224, 224], Image.LANCZOS)

    if transform is not None:
        image = transform(image).unsqueeze(0)
    return image


def generateCaption(image_tensor, vocab, encoder, decoder):
    # Generate an caption from the image
    feature = encoder(image_tensor)
    sampled_ids = decoder.sample(feature)
    sampled_ids = sampled_ids[0].cpu().numpy()  # (1, max_seq_length) -> (max_seq_length)

    # Convert word_ids to words
    sampled_caption = []
    for word_id in sampled_ids:
        word = vocab.idx2word[word_id]
        sampled_caption.append(word)
        if word == '<end>':
            break
    sentence = ' '.join(sampled_caption)

    return sentence



def main(args):
    # Image preprocessing
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.485, 0.456, 0.406),
                             (0.229, 0.224, 0.225))])

    transform_val = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])



    # Load vocabulary wrapper
    with open(args.vocab_path, 'rb') as f:
        vocab = pickle.load(f)

    # Load json-test-file
    #with open(args.test_json, 'r') as json_file:
    #    json_test = json.load(json_file)
    json_test = json.load(open('./ankle_test_data.json', 'r'))


    # Build models
    encoder = EncoderCNN(args.embed_size).eval()  # eval mode (batchnorm uses moving mean/variance)
    decoder = DecoderRNN(args.embed_size, args.hidden_size, len(vocab), args.num_layers)
    encoder = encoder.to(device)
    decoder = decoder.to(device)

    # Load the trained model parameters
    encoder.load_state_dict(torch.load(args.encoder_path))
    decoder.load_state_dict(torch.load(args.decoder_path))


    for jimg in json_test[40:50]:
        # Prepare an image
        image = load_image(jimg['file_paths'][0], transform)
        image_tensor = image.to(device)
        cap = generateCaption(image_tensor, vocab, encoder, decoder)
        print('Human cap: %s' % jimg['captions'][0])
        print('AI cap: %s' % cap)
        print('\n')
        image_show = Image.open(jimg['file_paths'][0])
        plt.imshow(np.asarray(image_show))
        plt.show()


if __name__ == '__main__':
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', type=str, required=True, help='input image for generating caption')
    parser.add_argument('--encoder_path', type=str, default='./models/encoder-2-1000.ckpt',
                        help='path for trained encoder')
    parser.add_argument('--decoder_path', type=str, default='./models/decoder-2-1000.ckpt',
                        help='path for trained decoder')
    parser.add_argument('--vocab_path', type=str, default='./data/vocab.pkl', help='path for vocabulary wrapper')
    parser.add_argument('--test_folder_path', type=str, default='./data/test_imgs', help='path for folder with testimgs')

    # Model parameters (should be same as paramters in train.py)
    parser.add_argument('--embed_size', type=int, default=256, help='dimension of word embedding vectors')
    parser.add_argument('--hidden_size', type=int, default=512, help='dimension of lstm hidden states')
    parser.add_argument('--num_layers', type=int, default=1, help='number of layers in lstm')
    args = parser.parse_args()
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--encoder_path', type=str, default='./models/encoder-5-335.ckpt',
                        help='path for trained encoder')
    parser.add_argument('--decoder_path', type=str, default='./models/decoder-5-335.ckpt',
                        help='path for trained decoder')
    parser.add_argument('--test_json', type=str, default='./radcap_data.json', help='path for json file with test imgs')
    parser.add_argument('--vocab_path', type=str, default='./data/vocab.pkl', help='path for vocabulary wrapper')

    # Model parameters (should be same as paramters in train.py)
    parser.add_argument('--embed_size', type=int, default=256, help='dimension of word embedding vectors')
    parser.add_argument('--hidden_size', type=int, default=512, help='dimension of lstm hidden states')
    parser.add_argument('--num_layers', type=int, default=1, help='number of layers in lstm')
    args = parser.parse_args()
    main(args)