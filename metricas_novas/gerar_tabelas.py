import os
import re
import csv
import glob

def parse_report(filepath):
    metrics = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Extract model name
    model_match = re.search(r'Modelo:\s*(.*?)\s*\|', content)
    if model_match:
        metrics['Modelo'] = model_match.group(1).strip()
    else:
        # Fallback to filename
        metrics['Modelo'] = os.path.basename(filepath).replace('relatorio_metrics_', '').replace('.txt', '')
        
    # Determine type (Cloud vs Local)
    # Check if the title is "Relatório Ollama Cloud" or if model name contains "cloud"
    is_cloud = 'Relatório Ollama Cloud' in content or 'cloud' in metrics['Modelo'].lower() or '-cloud' in os.path.basename(filepath).lower()
    metrics['Tipo'] = 'Cloud' if is_cloud else 'Local'

    # Extract Datasets
    datasets = ['SMS', 'Email']
    
    # Split content by Dataset
    sections = re.split(r'={50,}\n\s*(.*? Dataset)\s*\n={50,}', content)
    
    # Initialize all possible columns as empty string to avoid MissingKey errors
    columns = ['Acurácia', 'Precisão', 'Recall', 'Especificidade', 'F1-Score',
               'TP', 'FP', 'FN', 'TN',
               'Tempo_Média', 'Tempo_Desvio_Padrão', 'Total_Pipeline_Média']
    
    for ds in datasets:
        for col in columns:
            metrics[f'{ds}_{col}'] = ''
            
    current_ds = None
    for section in sections:
        if 'SMS Dataset' in section:
            current_ds = 'SMS'
            continue
        elif 'Email Dataset' in section:
            current_ds = 'Email'
            continue
            
        if current_ds:
            # Classification Metrics
            acuracia = re.search(r'Acurácia:\s*([0-9.]+%?)', section)
            precisao = re.search(r'Precisão:\s*([0-9.]+%?)', section)
            recall = re.search(r'Recall:\s*([0-9.]+%?)', section)
            especificidade = re.search(r'Especificidade:\s*([0-9.]+%?)', section)
            f1 = re.search(r'F1-Score:\s*([0-9.]+%?)', section)
            
            if acuracia: metrics[f'{current_ds}_Acurácia'] = acuracia.group(1)
            if precisao: metrics[f'{current_ds}_Precisão'] = precisao.group(1)
            if recall: metrics[f'{current_ds}_Recall'] = recall.group(1)
            if especificidade: metrics[f'{current_ds}_Especificidade'] = especificidade.group(1)
            if f1: metrics[f'{current_ds}_F1-Score'] = f1.group(1)
            
            # Confusion Matrix
            cm = re.search(r'TP=(\d+)\s+FP=(\d+)\s+FN=(\d+)\s+TN=(\d+)', section)
            if cm:
                metrics[f'{current_ds}_TP'] = cm.group(1)
                metrics[f'{current_ds}_FP'] = cm.group(2)
                metrics[f'{current_ds}_FN'] = cm.group(3)
                metrics[f'{current_ds}_TN'] = cm.group(4)
                
            # Inference Time
            tempo_media = re.search(r'Média:\s*([0-9.]+s)', section)
            tempo_desvio = re.search(r'Desvio Padrão:\s*([0-9.]+s)', section)
            total_pipeline = re.search(r'Total Pipeline \(média\):\s*([0-9.]+s)', section)
            
            if tempo_media: metrics[f'{current_ds}_Tempo_Média'] = tempo_media.group(1)
            if tempo_desvio: metrics[f'{current_ds}_Tempo_Desvio_Padrão'] = tempo_desvio.group(1)
            if total_pipeline: metrics[f'{current_ds}_Total_Pipeline_Média'] = total_pipeline.group(1)

    return metrics

def write_csv(data, filename):
    if not data:
        return
    fieldnames = list(data[0].keys())
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    print(f"Tabela gerada: {filename}")

def main():
    directory = os.path.dirname(os.path.abspath(__file__))
    files = glob.glob(os.path.join(directory, 'relatorio_metrics_*.txt'))
    
    all_metrics = []
    for f in files:
        metrics = parse_report(f)
        all_metrics.append(metrics)
        
    # Sort by model name
    all_metrics.sort(key=lambda x: x['Modelo'].lower())
    
    # Filter by type
    cloud_metrics = [m for m in all_metrics if m['Tipo'] == 'Cloud']
    local_metrics = [m for m in all_metrics if m['Tipo'] == 'Local']
    
    # Write tables
    write_csv(all_metrics, os.path.join(directory, 'tabela_1_todos_modelos.csv'))
    write_csv(cloud_metrics, os.path.join(directory, 'tabela_2_modelos_cloud.csv'))
    write_csv(local_metrics, os.path.join(directory, 'tabela_3_modelos_locais.csv'))
    
if __name__ == '__main__':
    main()
