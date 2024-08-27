from transformers import BertTokenizer, BertForMaskedLM, AutoTokenizer
import torch
import re, json
from tqdm import tqdm

tokenizer = AutoTokenizer.from_pretrained('/Users/kian/code/llmtupi/models/distilbert-NER-09-03-24_11')
model = BertForMaskedLM.from_pretrained('/Users/kian/code/llmtupi/models/distilbert-NER-09-03-24_11')
device = torch.device('mps')
# and move our model over to the selected device
model.to(device)

special_chars = "û î ŷ á é í ý ó ú ã ẽ ĩ ỹ õ ũ '".split(" ")
# Create a two-way dictionary
def normalize_tupi(x):
    # for i, char in enumerate(special_chars):
        # print(special_chars_map[char], char)
        # x = x.replace(char, f"w{i}q")
    return re.sub('\s+', ' ', x).strip()
def replace_outside_brackets(match):
    part = match.group()
    if part.startswith('[') and part.endswith(']'):
        return part  # Return the part unchanged if it's inside brackets
    # for i, char in enumerate(special_chars):
        # part = part.replace(f"w{i}q", f"{char}")
    return part
def navarroize_tupi(x):
    # Pattern to match text outside square brackets
    pattern = r'\[.*?\]|[^[\]]+'
    return re.sub(pattern, replace_outside_brackets, x)

import sys
sys.path.append('/Users/kian/code/nhe-enga/tupi')
from tupi import Noun
n = Noun('iru', '')
MAX_INPUT_LENGTH=36
def anotate(st, debug=False):
    # Now we will test the model with a sample sentence
    sentence = normalize_tupi(st).lower().replace(',', '').replace('.', '').replace('?', '').replace('!', '').replace('-', '').strip()
    inp_sent = navarroize_tupi(sentence)
    if debug:
        print("Input Phrase:\t\t", inp_sent)
    # Now we will use this sentence to predict the masked word
    inputs = tokenizer(sentence, return_tensors='pt', max_length=MAX_INPUT_LENGTH, truncation=True, padding='max_length')
    # print(inputs)
    # # Now we will test the model with a sample sentence
    # sentence = normalize_tupi("..[MASK] endé ruba. ixé nde ra'yra").replace('[mask]', '[MASK]')
    # # Now we will use this sentence to predict the masked word
    # inputs = tokenizer(sentence, return_tensors='pt')
    # print(inputs)
    inputs.to(device)
    # get logits of the prediction
    logits = model(**inputs).logits
    # get index of most likely prediction
    predicted_index = torch.argmax(logits[0, 3]).item()
    # Get a string representation of the most likely word
    pred = tokenizer.convert_ids_to_tokens([predicted_index])[0]
    # print(pred)
    # Now do rhat for all the predictions
    predicted_indices = torch.argmax(logits, dim=2)
    toks = tokenizer.convert_ids_to_tokens(predicted_indices[0])
    tl = "".join(toks).replace(' ##', '').replace('##', '').replace(' \' ', "'").replace("Ġ", " ").split('[PAD]')[0]
    out_pred = navarroize_tupi(tl)[5:-5]
    
    recon = eval(n.perform_recreate(out_pred))
    if debug:
        print("Inferred Breakdown:\t", out_pred)
        print("Reconstructed Phrase:\t", recon)
        print("Acertou?\t\t",inp_sent == recon.substantivo())
        print()
    return recon

not_working = []
# open docs/all_nouns_verbs.json into a list
with open('docs/all_nouns_verbs.json', 'r') as f:
    data = json.load(f)


# # run annotate on each string in data and save the results, use tqdm to track
# results = []
# for x in tqdm(data):
#     try:
#         results.append(anotate(x))
#     except Exception as e:
#         results.append("")
#         not_working.append((x, e))

# for i, res in enumerate(results):

#     vbt = res.aglutinantes[-2].verbete() if res else ""
#     if vbt != data[i]:
#         print("Diff: ", vbt, data[i])
#         not_working.append((data[i], vbt))

# for x, y in not_working:
#     print("VBT: ", x, "\t\t\t", y)