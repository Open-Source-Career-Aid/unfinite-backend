# Model parameters
from transformers import (
    Text2TextGenerationPipeline,
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
)


class KeyphraseGenerationPipeline(Text2TextGenerationPipeline):
    def __init__(self, model, keyphrase_sep_token=";", *args, **kwargs):
        super().__init__(
            model=AutoModelForSeq2SeqLM.from_pretrained(model),
            tokenizer=AutoTokenizer.from_pretrained(model),
            *args,
            **kwargs
        )
        self.keyphrase_sep_token = keyphrase_sep_token

    def postprocess(self, model_outputs):
        results = super().postprocess(
            model_outputs=model_outputs
        )
        return [[keyphrase.strip() for keyphrase in result.get("generated_text").split(self.keyphrase_sep_token) if keyphrase != ""] for result in results]

if __name__ == '__main__':

    # Load pipeline
    model_name = "ml6team/keyphrase-generation-t5-small-openkp"
    generator = KeyphraseGenerationPipeline(model=model_name)

    while True:
        text  = input("Enter text: ")
        kps = []
        lines = text.split('.')
        # Generate keyphrases
        for line in lines:
            kps.extend(generator(line)[0])
        print(kps)