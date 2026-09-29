import os
import json

path = 'app/extraction/vlm_extractor.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_extract_gemini = False
for line in lines:
    if line.strip().startswith("def _extract_gemini"):
        in_extract_gemini = True
        new_lines.append(line)
        new_lines.append("        mime_type = self._fix_mime_type(mime_type)\n")
        new_lines.append("        model = self.client.GenerativeModel(\n")
        new_lines.append("            model_name=self.gemini_model,\n")
        new_lines.append("            system_instruction=system_prompt,\n")
        new_lines.append("            generation_config={\"response_mime_type\": \"application/json\"}\n")
        new_lines.append("        )\n")
        new_lines.append("        \n")
        new_lines.append("        img = {\n")
        new_lines.append("            \"mime_type\": mime_type,\n")
        new_lines.append("            \"data\": image_bytes\n")
        new_lines.append("        }\n")
        new_lines.append("        \n")
        new_lines.append("        schema_json = json.dumps(schema_class.model_json_schema())\n")
        new_lines.append("        prompt_text = f\"Extract the requested information from this document. Return ONLY valid JSON matching this exact JSON schema (do not hallucinate fields, ensure required fields are present):\\n{schema_json}\"\n")
        new_lines.append("        response = model.generate_content([img, prompt_text])\n")
        new_lines.append("        \n")
        new_lines.append("        data = json.loads(response.text)\n")
        new_lines.append("        return schema_class.model_validate(data)\n")
        new_lines.append("\n")
    elif in_extract_gemini:
        if line.strip().startswith("def extract_hospital_bill"):
            in_extract_gemini = False
            new_lines.append(line)
    else:
        new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
