import json
import re
from typing import Any

from openai import OpenAI

from app.config import settings


class LLMService:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    @property
    def live(self) -> bool:
        return bool(self.client and not settings.demo_mode)

    def _response_text(self, prompt: str) -> str:
        if not self.client:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        response = self.client.responses.create(model=settings.chat_model, input=prompt)
        return response.output_text

    @staticmethod
    def _extract_json(text: str) -> Any:
        text = text.strip()
        fenced = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.S | re.I)
        if fenced:
            text = fenced.group(1).strip()
        first_array = text.find("[")
        first_object = text.find("{")
        starts = [x for x in (first_array, first_object) if x >= 0]
        if starts:
            text = text[min(starts):]
        # trim common prose after the JSON payload
        for end_char in ("]", "}"):
            pos = text.rfind(end_char)
            if pos >= 0:
                candidate = text[: pos + 1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    pass
        return json.loads(text)

    def generate_questions(self, role: str, difficulty: str, count: int, context: str) -> list[dict]:
        if not self.live:
            return self._demo_questions(role, difficulty, count, context)

        prompt = f"""You are a senior technical interviewer. Create exactly {count} interview questions for a {role} candidate at {difficulty} difficulty.
Use ONLY the supplied resume/job-description evidence to personalize the questions. Mix technical, system-design, behavioral, debugging, and project-depth questions when the evidence supports them.

EVIDENCE:
{context}

Return only a JSON array. Every item must have these string keys: category, question, why_asked.
Avoid trivia. Ask questions that let the candidate prove depth and connect answers to their actual experience."""
        payload = self._extract_json(self._response_text(prompt))
        if not isinstance(payload, list):
            raise ValueError("Question generator did not return a JSON array")
        return payload[:count]

    def evaluate_answer(self, role: str, question: str, answer: str, context: str) -> dict:
        if not self.live:
            return self._demo_evaluation(question, answer)

        prompt = f"""You are evaluating a candidate interviewing for {role}.
Score the answer from 0 to 100. Ground technical expectations in the supplied evidence, but do not penalize a candidate for not inventing details that are not present.

QUESTION:
{question}

CANDIDATE ANSWER:
{answer}

RETRIEVED EVIDENCE:
{context}

Return ONLY one JSON object with these fields:
overall_score, relevance_score, clarity_score, structure_score, technical_score (numbers 0-100),
strengths (array of 2-4 short strings), improvements (array of 2-4 short strings), stronger_answer (a concise first-person answer the candidate could give, usually 120-220 words).
For behavioral/project questions reward STAR-style structure, concrete decisions, tradeoffs, and measurable impact. For technical questions reward correctness, tradeoffs, failure modes, and production considerations."""
        payload = self._extract_json(self._response_text(prompt))
        if not isinstance(payload, dict):
            raise ValueError("Evaluator did not return a JSON object")
        return payload

    def _demo_questions(self, role: str, difficulty: str, count: int, context: str) -> list[dict]:
        lower = context.lower()
        bank = []
        if "fastapi" in lower or "flask" in lower:
            bank.append(("Backend", "Walk me through one API you designed end to end. How did you structure validation, service logic, database access, error handling, and tests?"))
        if "react" in lower:
            bank.append(("Frontend", "Describe a React feature you owned. How did you manage server state, local state, loading/error states, and component boundaries?"))
        if "aws" in lower:
            bank.append(("Cloud", "Design a production deployment for this application on AWS. Which services would you choose, and how would you handle secrets, scaling, observability, and rollback?"))
        if "redis" in lower:
            bank.append(("Performance", "Where would Redis help in your architecture, and what cache invalidation or consistency problems would you plan for?"))
        if "postgres" in lower or "sql" in lower:
            bank.append(("Database", "Tell me about a database performance issue you would expect at scale. How would you detect it and decide between indexing, query changes, caching, or schema changes?"))
        bank.extend([
            ("Project depth", f"Choose the project most relevant to this {role} role. What was the hardest engineering decision you personally made, what alternatives did you reject, and why?"),
            ("System design", "Design a scalable interview-coaching platform that stores resumes, generates personalized questions, and evaluates answers. Explain the data model, APIs, async work, and failure handling."),
            ("Debugging", "A release causes API latency to jump from 200 ms to 2 seconds while CPU stays normal. How would you investigate this systematically?"),
            ("Behavioral", "Tell me about a time requirements were ambiguous. How did you reduce uncertainty while still delivering quickly?"),
            ("Quality", "What does production-grade mean to you? Give concrete examples covering testing, security, observability, deployment, and maintainability."),
        ])
        result = []
        for index in range(count):
            category, question = bank[index % len(bank)]
            result.append({
                "category": category,
                "question": question,
                "why_asked": f"Tests {difficulty}-level depth for the {role} role using skills found in the uploaded material.",
            })
        return result

    def _demo_evaluation(self, question: str, answer: str) -> dict:
        words = answer.split()
        length_score = min(100, 35 + len(words) * 0.65)
        detail_markers = sum(token in answer.lower() for token in ["because", "tradeoff", "result", "improved", "reduced", "measured", "tested", "monitor", "latency", "scale"])
        structure_markers = sum(token in answer.lower() for token in ["situation", "task", "action", "result", "first", "then", "finally"])
        relevance = min(96, length_score + detail_markers * 2)
        clarity = min(94, 58 + min(len(words), 110) * 0.25)
        structure = min(95, 55 + structure_markers * 6)
        technical = min(96, 58 + detail_markers * 5)
        overall = round((relevance + clarity + structure + technical) / 4, 1)
        return {
            "overall_score": overall,
            "relevance_score": round(relevance, 1),
            "clarity_score": round(clarity, 1),
            "structure_score": round(structure, 1),
            "technical_score": round(technical, 1),
            "strengths": ["The answer addresses the question directly.", "You provided enough detail to understand your approach."],
            "improvements": ["Add one concrete tradeoff or decision you personally made.", "Finish with a measurable result or production impact."],
            "stronger_answer": "I would answer this by first stating the situation and the engineering goal, then describing the decision I personally owned. I would explain the alternatives I considered, why I chose the final approach, and the main tradeoff. Next I would describe implementation details that prove depth—data flow, validation, testing, observability, and failure handling where relevant. I would close with the outcome using a concrete metric such as latency, reliability, deployment frequency, defect reduction, or user impact. That structure keeps the answer concise while showing both technical judgment and ownership.",
        }


llm_service = LLMService()
