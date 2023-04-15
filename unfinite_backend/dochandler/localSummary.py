from transformers import AutoTokenizer, BartForConditionalGeneration, PegasusXForConditionalGeneration

# model = PegasusXForConditionalGeneration.from_pretrained("google/pegasus-x-base")
# tokenizer = AutoTokenizer.from_pretrained("google/pegasus-x-large")

model = BartForConditionalGeneration.from_pretrained("facebook/bart-large-cnn")
tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")

def summarywithContext(text, context):
    '''
    eg.
    Context: rank of the height.
    Text: The tower is 324 metres (1,063 ft) tall, about the same height as an 81-storey building, and the tallest structure in Paris. Its base is square, measuring 125 metres (410 ft) on each side. During its construction, the Eiffel Tower surpassed the Washington Monument to become the tallest man-made structure in the world, a title it held for 41 years until the Chrysler Building in New York City was finished in 1930. It was the first structure to reach a height of 300 metres. Due to the addition of a broadcasting aerial at the top of the tower in 1957, it is now taller than the Chrysler Building by 5.2 metres (17 ft). Excluding transmitters, the Eiffel Tower is the second tallest free-standing structure in France after the Millau Viaduct.

    [Generated Summary]: The tower is 324 metres (1,063 ft) tall, about the same height as an 81-storey building . It was the first structure to reach a height of 300 metres . It is now taller than the Chrysler Building by 5.2 metres (17 ft) Excluding transmitters, it is the second tallest free-standing structure in France after the Millau Viaduct .
    '''
    # bart
    prompt = f"Context: {context}\nText: {text}"
    inputs = tokenizer([prompt], return_tensors='pt', max_length=1024, truncation=True)
    summary_ids = model.generate(inputs["input_ids"], num_beams=2, min_length=0, max_length=100)
    return tokenizer.batch_decode(summary_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]

    # # pegasus
    # inputs = tokenizer([prompt], max_length=1024, return_tensors="pt", truncation=True)

    # # Generate Summary
    # summary_ids = model.generate(inputs["input_ids"], num_beams=4, max_length=100, early_stopping=True)
    # return tokenizer.batch_decode(summary_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]

# if __name__ == '__main__':

#     while True:
#         text = input("Enter text to summarize: ")
#         context = input("Enter context: ")
#         print(summarywithContext(text, context))