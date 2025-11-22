from typing import List, Dict

def load_data(raw_input: List[Dict]) -> List[Dict]:
    """
    Standardizes raw input into a list of dicts with 'id' and 'text'.
    Accepts Slack messages, docs, JSON, or any text-like input.
    """
    standardized = []
    for idx, item in enumerate(raw_input):
        text = item.get('text') or item.get('message') or str(item)
        standardized.append({
            'id': str(idx),
            'text': text
        })
    return standardized
