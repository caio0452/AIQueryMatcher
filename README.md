
## How to use this:

1. Set the OPENAI_API_KEY enviroment variable

2. Create an ETAClassifier: 

```python
classifier =  await eta_classifier.EtaClassifier.with_openai(
	api_key=api_key,
	model="gpt-3.5-turbo"
)
```
3. Fetch the classification result

```python
classification = await classifier.classify(query)
print(classification.belongs_to_class)
```
This will be true if the query is indeed an ETA question.
You can use any OpenAI chat completion model, currently `gpt-3.5-turbo` and `gpt-4o` are the more relevant ones.

## How does this work?

The ETAClassifier has 3 steps:
1. Check if needed keywords are there. If not, stop, it's not an ETA question
2. Then, check if the general wording is similar enough to a reference question using word embeddings (cheap, less accurate). If not, stop, it's not an ETA question
3. Then, use a LLM to check more accurately if the query is an ETA question (expensive, more accurate)

## How much does it cost to run?

This repo uses GPT-3.5-turbo. The costs depending on how many steps the queries go through.
The keyword check step is free, it's string searches.
The similarity step costs around $0.033 per million text characters
The keyword check steps costs around $0.3 every thousand messages that look similar to the reference question. With GPT-4o, this costs 10x as much. 

## How to make my own classifier for other types of question?

### Step 1: Adapt the Classification Prompt

Make a copy of the eta_classifier class, with a name of your choice. You need to modify the classification prompt to fit your use case. The prompt is used by the LLM to classify the query.

1. Create a new constant for your classification prompt, with user-assistant back and forth

```python
YOUR_CLASSIFICATION_PROMPT = [
    {
        "role": "system",
        "content": 
"""
You're a bot that classifies what the user says, to determine [your classification criteria].
Given a query, return only a JSON containing:
* reasoning: short details about the classification process
* [your_category_1]: [description of category 1]
* [your_category_2]: [description of category 2]
* [add as many categories as you need]
"""
    },
    # Add a few examples here to guide the LLM
]
```

2. Customize the system message and add your own categories. Note that the reasoning step is important to reduce hallucinations.
3. Provide a few examples to guide the LLM in classifying queries correctly. If they turn out wrong in edge cases during your test, experiment with adding that to the examples.

### Step 2: Adjust the Similarity Check

Modify the similarity check to better suit your needs:

1. Change the reference question in the `with_openai` class method:

```python
REFERENCE_PHRASE = "Your reference phrase here"
```

2. Adjust the similarity threshold in the `SimilarityCheckStep`:

```python
SimilarityCheckStep(client=client, reference_embedding=ref_emb, threshold=0.4)  # This is an experimental value
```

### Step 3: Implement Your Custom LLM Check

Create a new class that derives from `ClassificationStep`. This is used check the JSON fields that the AI will return, according to your use case that you defined in the prompt examples:

```python
class YourCustomLLMCheckStep(ClassificationStep):
    def __init__(self, *, client: AsyncOpenAI, classification_prompt: list[dict[str, Any]], model="gpt-4"):
        self._client = client
        self._classification_prompt = classification_prompt
        self._model = model

    async def run(self, query: str) -> ClassificationStep.Result:
        prompt = self._classification_prompt.copy()
        prompt.append({
            "role": "user",
            "content": query
        })
        
        llm_classification_resp = await self._client.chat.completions.create(
            model=self._model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=prompt
        )
        
        llm_resp = llm_classification_resp.choices[0].message.content
        llm_resp_json = json.loads(llm_resp)
        
        # Check your custom JSON fields here
        if not self._check_custom_conditions(llm_resp_json):
            return ClassificationStep.Result(success=False, fail_reason=f"failed_llm_check, got {llm_resp}")
        else:
            return ClassificationStep.Result(success=True, fail_reason=None)

    def _check_custom_conditions(self, json_response: dict) -> bool:
        # Implement your custom checks here
        # Return True if all conditions are met, False otherwise
        pass
```

### Step 4: Create Your Custom Classifier

Now, create your custom classifier that uses the new components:

```python
class YourCustomClassifier(QueryClassifier):
    def __init__(self, *, check_steps: list[ClassificationStep]):
        self._check_steps = check_steps

    @classmethod
    async def with_openai(cls, *, api_key: str, model: str = "gpt-4", api_base: str | None = None) -> "YourCustomClassifier":
        REFERENCE_PHRASE = "Your reference phrase here"
        client = AsyncOpenAI(api_key=api_key, base_url=api_base)
        emb_resp = await client.embeddings.create(
            model="text-embedding-3-large", 
            input=REFERENCE_PHRASE
        )
        ref_emb = emb_resp.data[0].embedding

        return cls(
            check_steps=[
                KeywordCheckStep(must_have_all_keywords=["your", "keywords"], must_have_any_keywords=[]),
                SimilarityCheckStep(client=client, reference_embedding=ref_emb, threshold=0.5),
                YourCustomLLMCheckStep(client=client, classification_prompt=YOUR_CLASSIFICATION_PROMPT, model=model)
            ]
        )

    async def classify(self, query: str) -> QueryClassifier.QueryClassificationResult:
        # This method can remain the same as in EtaClassifier
        # ...
```

### Usage

To use your new custom classifier:

```python
async def main():
    classifier = await YourCustomClassifier.with_openai(api_key="your_api_key_here")
    result = await classifier.classify("Your test query here")
    print(result.belongs_to_class)
```

