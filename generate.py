from __future__ import print_function
import argparse
import logging

import torch
from torch.nn import functional as F

from preprocess import pad_sequences, tokenize, detokenize
from src.preprocessing import data_utils
from train import load_checkpoint

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)8.8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def translate(model, text, src_tokenizer_path, trg_tokenizer_path, device, max_len):
    src_tensor = pad_sequences(tokenize([text], src_tokenizer_path), max_len).to(device)
    outputs = [data_utils.BOS_IDX]
    model.eval()
    for i in range(max_len):
        trg_pred_tensor = torch.LongTensor(outputs).unsqueeze(1).to(device)

        with torch.no_grad():
            output = model(src_tensor.T, trg_pred_tensor)
            output = F.softmax(output, dim=-1)

        best_guess = output.argmax(2)[-1, :].item()
        outputs.append(best_guess)

        if best_guess == data_utils.EOS_IDX:
            break

    translated = detokenize(outputs[1:-1], trg_tokenizer_path)
    return translated[0]


def main(cfg):
    logger.info("SRC: " + cfg.src_sentence)
    _, model = load_checkpoint(cfg.model_path, load_optimizer=False, load_scheduler=False)
    device = torch.device("cuda") if cfg.use_cuda else torch.device("cpu")

    logger.info("TRG: " + translate(model, cfg.src_sentence, cfg.src_tokenizer_path, cfg.trg_tokenizer_path,
                                    device, cfg.max_seq_len))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Translation hyperparams')
    parser.add_argument('--model-path', required=True, type=str, help='Path to the test data')
    parser.add_argument('--src-sentence', required=True, type=str, help='Path to an existing vocabulary file')
    parser.add_argument('--max-seq-len', type=int, default=100,
                        help='Maximum len of sentence to generate. Counted in subwords')
    parser.add_argument('--src-tokenizer-path', required=True, type=str, help='Path to source tokenizer model')
    parser.add_argument('--trg-tokenizer-path', required=True, type=str, help='Path to target tokenizer model')
    parser.add_argument('--use-cuda', type=bool, default=False)
    cfg = parser.parse_args()
    logger.info(cfg)
    main(cfg)
    logger.info('Terminated')

