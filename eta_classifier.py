from classification import QueryClassifier, ClassificationStep, SimilarityCheckStep, KeywordCheckStep
from openai import AsyncOpenAI
from typing import Any
import json

ETA_CLASSIFICATION_PROMPT = [
    {
        "role": "system",
        "content": 
"""
You're a bot that classifies what the user says, to determine if they're asking for a release time or estimates for Paper 1.21 release, that is currently not out. An ETA is another word for an estimate.
Given a query, return only a JSON containing :
* reasoning: short details as to whether if the sentence is readable, what the user is asking or saying, and whether this is or not asking for a release date or estimate
* readable: whether the sentence is clear and readable or not
* asking_release_eta: will be true if the user is asking when the release will happen, or for estimates (ETA). Will be false if the user is simply mentioning a realease
* project_name: The name of the project if any, may be "none"
* version: The version mentioned if any, may be "none"
"""
    },
    {
        "role": "user",
        "content": "hi, do you know when 1.21 will be out?"
    },
    {
        "role": "assistant",
        "content": "{\"reasoning\": \"The sentence is readable, and the user is asking when an unspecified project for version 1.21 will be out. Therefore, they are asking for a release date or estimate\", \"readable\": true, \"asking_release_eta\": true, \"project_name\": \"none\", \"version\": \"1.21\"}"
    },
    {
        "role": "user",
        "content": "I would like to know when Paper will update"
    },
    {
        "role": "assistant",
        "content": "{\"reasoning\": \"The sentence is clear and readable. The user would like to know when Paper, for a version they did not specify, will be updated. Thus, they are indeed asking for a timeframe.\", \"readable\": true, \"asking_release_eta\": true, \"project_name\": \"Paper\", \"version\": \"none\"}"
    },
    {
        "role": "user",
        "content": "I'm not sure when the Paper 1.21 release will drop"
    },
    {
        "role": "assistant",
        "content": "{\"reasoning\": \"The sentence is readable, and the user is just stating they do not know when Paper version 1.21 will release, not requesting any estimates. So, the user is not asking for dates or estimates.\", \"readable\": true, \"asking_release_eta\": false, \"project_name\": \"Paper\", \"version\": \"1.21\"}"
    },
    {
        "role": "user",
        "content": "guys can you believe 1.21 is released?????"
    },
    {
        "role": "assistant",
        "content": "{\"reasoning\": \"The sentence is readable and the user is expressing disbelief that version 1.21 is released. They are not asking for a release date or estimate.\", \"readable\": true, \"asking_release_eta\": false, \"project_name\": \"none\", \"version\": \"1.21\"}"
    },
    {
        "role": "user",
        "content": "guyssdys 1.2287 uwybeg"
    },
    {
        "role": "assistant",
        "content": "{\"reasoning\": \"The sentence is not readable due to gibberish content and unclear intent.\", \"readable\": false, \"asking_release_eta\": false, \"project_name\": \"none\", \"version\": \"none\"}"
    },
    {
        "role": "user",
        "content": "vanilla 1.20 out when????"
    },
    {
        "role": "assistant",
        "content": "{\"reasoning\": \"The sentence is readable and the user is asking when version 1.20 of something called vanilla will be out, which is a request for a release date or estimate.\", \"readable\": true, \"asking_release_eta\": true, \"project_name\": \"vanilla\", \"version\": \"1.20\"}"
    },
    {
        "role": "user",
        "content": "I hate it when people keep asking if 1.21 will come out"
    },
    {
        "role": "assistant",
        "content": "{\"reasoning\": \"The sentence is readable and the user is expressing annoyance at others asking about the release of version 1.21. They are not asking for a release date or estimate themselves.\", \"readable\": true, \"asking_release_eta\": false, \"project_name\": \"none\", \"version\": \"1.21\"}"
    }
]

class EtaClassifier(QueryClassifier):
    def __init__(
            self,
            *,
            check_steps: list[ClassificationStep]
        ):
        """
        Represents a base ETA query classifier. Use the convenience factory methods to initialize.
        """
        self._check_steps = check_steps

    @classmethod
    async def with_openai(cls, *, api_key: str, model: str = "gpt-4o", api_base: str | None = None) -> "EtaClassifier":
        REFERENCE_ETA_PHRASE = "Is there any ETA / estimate / progress on when 1.21 will release / come out?"
        client = AsyncOpenAI(api_key=api_key, base_url=api_base)
        emb_resp = await client.embeddings.create(
            model="text-embedding-3-large", 
            input=REFERENCE_ETA_PHRASE
        )
        ref_emb = emb_resp.data[0].embedding

        return cls(
            check_steps=[
                KeywordCheckStep(must_have_all_keywords=["paper", "1.21"], must_have_any_keywords=[]),
                SimilarityCheckStep(client=client, reference_embedding=ref_emb),
                LLMClassificationStep(client=client, classification_prompt=ETA_CLASSIFICATION_PROMPT, model=model)
            ]
        )

    async def classify(self, query: str) -> QueryClassifier.QueryClassificationResult:
        belongs_to_class = True
        fail_reason = None
        steps_results = []

        for step in self._check_steps:
            result = await step.run(query)
            steps_results.append(result)
            if not result.success:
                belongs_to_class = False
                fail_reason = result.fail_reason

        return QueryClassifier.QueryClassificationResult(
            belongs_to_class=belongs_to_class,
            fail_reason=fail_reason,
            steps_results=steps_results
        )

class LLMClassificationStep(ClassificationStep):
    def __init__(self, *, client: AsyncOpenAI, classification_prompt: dict[str, Any], model="gpt-4o"):
        self._client = client
        self._classification_prompt = classification_prompt
        self._model = model

    async def run(self, query: str) -> ClassificationStep.Result:
        prompt = ETA_CLASSIFICATION_PROMPT
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
        
        asking_eta: bool = llm_resp_json["asking_release_eta"]
        proj_name: str = llm_resp_json["project_name"]
        version: str = llm_resp_json["version"]
        readable: bool = llm_resp_json["readable"]
        
        if any([
            not asking_eta,
            not readable,
            proj_name.lower() != "paper",
            version != "1.21",    
        ]):
            return ClassificationStep.Result(success=False, fail_reason=f"failed_llm_check, got {llm_resp}")
        else:
            return ClassificationStep.Result(success=True, fail_reason=None)