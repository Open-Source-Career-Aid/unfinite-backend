from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import pickle

# device = "cuda"

tokenizer = AutoTokenizer.from_pretrained("humarin/chatgpt_paraphraser_on_T5_base")

model = AutoModelForSeq2SeqLM.from_pretrained("humarin/chatgpt_paraphraser_on_T5_base")
def paraphrase(
    question,
    num_beams=5,
    num_beam_groups=5,
    num_return_sequences=5,
    repetition_penalty=10.0,
    diversity_penalty=3.0,
    no_repeat_ngram_size=2,
    temperature=0.7,
    max_length=128
):
    input_ids = tokenizer(
        f'paraphrase: {question}',
        return_tensors="pt", padding="longest",
        max_length=max_length,
        truncation=True,
    ).input_ids
    
    outputs = model.generate(
        input_ids, temperature=temperature, repetition_penalty=repetition_penalty,
        num_return_sequences=num_return_sequences, no_repeat_ngram_size=no_repeat_ngram_size,
        num_beams=num_beams, num_beam_groups=num_beam_groups,
        max_length=max_length, diversity_penalty=diversity_penalty
    )

    res = tokenizer.batch_decode(outputs, skip_special_tokens=True)

    return res

if __name__ == "__main__":

    text = 'what is the summary of the paper?'

    paraphrases = set(paraphrase(text))

    i = 0

    while True:

        i += 1
        print(i)

        temp  = paraphrases.copy()
        
        for p in temp:
            new_paraphrases = set(paraphrase(p))
            paraphrases = paraphrases.union(new_paraphrases)
        
        print('Len:', len(paraphrases))
        if len(paraphrases) >= 100:
            break
        if i > 50:
            break
    
    # save to pickle
    with open('static/paraphrases.pkl', 'wb') as f:
        pickle.dump(paraphrases, f)