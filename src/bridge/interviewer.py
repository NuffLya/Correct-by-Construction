from typing import Any, Optional

from .llm_client import OllamaClient
from .spec_builder import build_spec_from_llm_response, parse_entity_from_text, parse_service_from_text


SYSTEM_PROMPT = """You are a technical analyst collecting a formal system specification.
Your task is to ask clarifying questions and extract structured information.
Answer concisely. Use the format:
- Entity: entity_name
  - field: type
  - invariant: expression
- Service: service_name
  - input name: type
  - pre: precondition
  - post: postcondition
Answer only the question asked, without extra explanation."""


class SpecificationInterviewer:

    def __init__(self, llm: OllamaClient) -> None:
        self.llm = llm
        self._messages: list[dict[str, str]] = []

    def _ask(self, question: str, context: Optional[str] = None) -> str:
        prompt = question
        if context:
            prompt = f"Context:\n{context}\n\nQuestion: {question}"

        if not self._messages:
            self._messages.append({"role": "system", "content": SYSTEM_PROMPT})

        self._messages.append({"role": "user", "content": prompt})
        response = self.llm.chat_sync(self._messages, temperature=0.5, max_tokens=2048)
        self._messages.append({"role": "assistant", "content": response})
        return response

    def conduct_interview(self, domain: str) -> dict[str, Any]:
        self._messages = []

        q1 = (
            f"Describe the domain: {domain}. "
            "What are the main entities in the system? "
            "For each entity specify: name, fields (name: type), invariants (conditions that must always hold). "
            "Format: Entity Name, fields, invariant expression."
        )
        entities_response = self._ask(q1)

        q2 = (
            "What main operations (services) are performed on these entities? "
            "For each operation: name, input parameters (name: type), preconditions (pre), postconditions (post). "
            "Format: Service Name, inputs, pre conditions, post conditions."
        )
        services_response = self._ask(q2, context=entities_response)

        return build_spec_from_llm_response(domain, entities_response, services_response)

    def refine_with_question(self, spec: dict[str, Any], question: str) -> dict[str, Any]:
        context = _spec_to_context(spec)
        response = self._ask(question, context=context)

        entity = parse_entity_from_text(response)
        if entity and entity not in [e for e in spec.get("entities", []) if e.get("name") == entity.get("name")]:
            for i, e in enumerate(spec.get("entities", [])):
                if e.get("name") == entity.get("name"):
                    spec["entities"][i] = entity
                    break
            else:
                spec.setdefault("entities", []).append(entity)

        service = parse_service_from_text(response)
        if service and service not in [s for s in spec.get("services", []) if s.get("name") == service.get("name")]:
            for i, s in enumerate(spec.get("services", [])):
                if s.get("name") == service.get("name"):
                    spec["services"][i] = service
                    break
            else:
                spec.setdefault("services", []).append(service)

        return spec

    def ask_about_counterexample(self, counterexample_description: str) -> str:
        prompt = (
            "A potentially suspicious scenario was found:\n\n"
            f"{counterexample_description}\n\n"
            "Is this scenario valid in the business logic? "
            "Answer briefly: yes/no and clarify if needed."
        )
        return self._ask(prompt)


def _spec_to_context(spec: dict[str, Any]) -> str:
    lines = []
    for e in spec.get("entities", []):
        lines.append(f"Entity {e.get('name', '')}: {e.get('fields', [])}, invariants: {e.get('invariants', [])}")
    for s in spec.get("services", []):
        lines.append(f"Service {s.get('name', '')}: {s.get('inputs', [])}, pre: {s.get('preconditions', [])}, post: {s.get('postconditions', [])}")
    return "\n".join(lines)
