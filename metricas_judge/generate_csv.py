import os
import csv
import re

directory = r"c:\Users\pedro\OneDrive\Documentos\Estudos-de-programaçaõ\zap-spam-detector\metricas_judge"

def parse_file(filepath):
    data = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract Modelo Principal and Judge
    m_modelo = re.search(r"Modelo Principal:\s*(.+?)\s*\|\s*Judge:\s*(.+)", content)
    if m_modelo:
        data['Modelo Principal'] = m_modelo.group(1).strip()
        data['Judge'] = m_modelo.group(2).strip()
    else:
        # Fallback if the format is slightly different
        m_modelo2 = re.search(r"Modelo Principal:\s*(.*)", content)
        if m_modelo2:
            data['Modelo Principal'] = m_modelo2.group(1).strip()
        data['Judge'] = ""

    datasets = ["SMS Dataset", "Email Dataset"]
    
    for ds in datasets:
        # Extract section
        section_pattern = rf"=\n\s*{ds}\n.*?=======================================================(.*?)(?=\n=======================================================|$)"
        if ds == "Email Dataset":
            section_pattern = rf"=\n\s*{ds}\n.*?=======================================================(.*)"
            
        m_section = re.search(section_pattern, content, re.DOTALL)
        if not m_section:
            # Fallback regex
            idx = content.find(ds)
            if idx != -1:
                end_idx = content.find("===============", idx)
                if end_idx == -1:
                    end_idx = len(content)
                section_text = content[idx:end_idx]
            else:
                section_text = ""
        else:
            section_text = m_section.group(1)

        def extract_metric(name, pattern):
            m = re.search(pattern, section_text)
            if m:
                data[f"{ds}_{name}"] = m.group(1).strip()
            else:
                data[f"{ds}_{name}"] = ""

        extract_metric("Acuracia", r"Acuracia:\s*([\d\.]+)%")
        extract_metric("Precisao", r"Precisao:\s*([\d\.]+)%")
        extract_metric("Recall", r"Recall:\s*([\d\.]+)%")
        extract_metric("Especificidade", r"Especificidade:\s*([\d\.]+)%")
        extract_metric("F1-Score", r"F1-Score:\s*([\d\.]+)%")
        
        m_tp = re.search(r"TP=(\d+)\s+FP=(\d+)\s+FN=(\d+)\s+TN=(\d+)", section_text)
        if m_tp:
            data[f"{ds}_TP"] = m_tp.group(1)
            data[f"{ds}_FP"] = m_tp.group(2)
            data[f"{ds}_FN"] = m_tp.group(3)
            data[f"{ds}_TN"] = m_tp.group(4)
        else:
            data[f"{ds}_TP"] = ""
            data[f"{ds}_FP"] = ""
            data[f"{ds}_FN"] = ""
            data[f"{ds}_TN"] = ""

        # Estatisticas do Judge
        extract_metric("Judge_Confirmacoes", r"Confirmacoes:\s*(\d+)")
        extract_metric("Judge_Correcoes", r"Correcoes:\s*(\d+)")
        
        # Tempo Modelo Principal
        idx_mp = section_text.find("Tempo de Inferencia - Modelo Principal")
        if idx_mp != -1:
            m_tempo_mp = re.search(r"Media:\s*([\d\.]+s)", section_text[idx_mp:idx_mp+500])
            data[f"{ds}_Tempo_MP_Media"] = m_tempo_mp.group(1) if m_tempo_mp else ""
            m_ic_mp = re.search(r"IC 95%:\s*(.+)", section_text[idx_mp:idx_mp+500])
            data[f"{ds}_Tempo_MP_IC95"] = m_ic_mp.group(1).strip() if m_ic_mp else ""
        else:
            data[f"{ds}_Tempo_MP_Media"] = ""
            data[f"{ds}_Tempo_MP_IC95"] = ""

        # Tempo Judge
        idx_j = section_text.find("Tempo de Inferencia - Judge")
        if idx_j != -1:
            m_tempo_j = re.search(r"Media:\s*([\d\.]+s)", section_text[idx_j:idx_j+500])
            data[f"{ds}_Tempo_Judge_Media"] = m_tempo_j.group(1) if m_tempo_j else ""
            m_ic_j = re.search(r"IC 95%:\s*(.+)", section_text[idx_j:idx_j+500])
            data[f"{ds}_Tempo_Judge_IC95"] = m_ic_j.group(1).strip() if m_ic_j else ""
        else:
            data[f"{ds}_Tempo_Judge_Media"] = ""
            data[f"{ds}_Tempo_Judge_IC95"] = ""

        # Total Pipeline
        extract_metric("Total_Pipeline", r"Total Pipeline \(media\):\s*([\d\.]+s)")
        
    return data

results = []
for filename in os.listdir(directory):
    if filename.endswith('.txt') and filename.startswith('relatorio_metrics_'):
        filepath = os.path.join(directory, filename)
        try:
            parsed_data = parse_file(filepath)
            parsed_data['Arquivo'] = filename
            results.append(parsed_data)
        except Exception as e:
            print(f"Error parsing {filename}: {e}")

if results:
    # Get all keys to use as headers
    keys = list(results[0].keys())
    # Ensure 'Arquivo' is the first column, then 'Modelo Principal', 'Judge'
    headers = ['Arquivo', 'Modelo Principal', 'Judge']
    for k in keys:
        if k not in headers:
            headers.append(k)
            
    csv_path = os.path.join(directory, "resumo_metricas_modelos.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in results:
            writer.writerow(r)
    print(f"CSV criado com sucesso em: {csv_path}")
else:
    print("Nenhum dado encontrado.")
