from abc import ABC, abstractmethod
from openai import AsyncOpenAI
import numpy as np

class ClassificationStep(ABC):
    class Result:
        def __init__(self, *, success: bool, fail_reason: str | None = None):
            self.success = success
            self.fail_reason = fail_reason

    @abstractmethod
    async def run(self, query: str) -> Result:
        raise NotImplementedError()

class QueryClassifier(ABC):
    class QueryClassificationResult:
        def __init__(self, *, belongs_to_class: bool, fail_reason: str | None, steps_results: list[ClassificationStep.Result]):
            self.belongs_to_class = belongs_to_class
            self.fail_reason = fail_reason   
            self.steps_results = steps_results    

    @abstractmethod
    async def classify(self, query: str) -> QueryClassificationResult:
        raise NotImplementedError()

class KeywordCheckStep(ClassificationStep):
    def __init__(self, must_have_all_keywords: list[str], must_have_any_keywords: list[str], case_sentive=False):
        self._must_have_all_keywords = must_have_all_keywords
        self._must_have_any_keywords = must_have_any_keywords
        self._case_sensitive = case_sentive

    async def run(self, query: str) -> ClassificationStep.Result:
        if self._case_sensitive:
            has_all_keywords = all(keyword in query for keyword in self._must_have_all_keywords)
            has_any_keyword = len(self._must_have_any_keywords) == 0 or \
                 any(keyword in query for keyword in self._must_have_any_keywords)
        else:
            has_all_keywords = all(keyword.lower() in query.lower() for keyword in self._must_have_all_keywords)
            has_any_keyword = len(self._must_have_any_keywords) == 0 or \
                 any(keyword in query for keyword in self._must_have_any_keywords)
            
        if not has_all_keywords:
            return ClassificationStep.Result(
                success=False, 
                fail_reason=f"Must have all keywords in {', '.join(self._must_have_all_keywords)}"
            )

        if not has_any_keyword:
            return ClassificationStep.Result(
                success=False, 
                fail_reason=f"Must have any keyword in {', '.join(self._must_have_any_keywords)}"
            )

        return ClassificationStep.Result(success=True, fail_reason=None)

class SimilarityCheckStep(ClassificationStep):
    def __init__(self, *, client: AsyncOpenAI, reference_embedding: list[float], min_text_similarity: float = 0.4):
        self._client = client
        self._min_text_similarity = min_text_similarity
        self._reference_embedding = reference_embedding

    async def run(self, query: str) -> ClassificationStep.Result:
        query_emb = await self._client.embeddings.create(
            model="text-embedding-3-large", 
            input=query
        )
        similarity = np.dot(query_emb.data[0].embedding, self._reference_embedding)
        if similarity > self._min_text_similarity:
            return ClassificationStep.Result(success=True, fail_reason=None)
        else:
            return ClassificationStep.Result(success=False, fail_reason=f"Needed similarity {self._min_text_similarity}, got {similarity}")