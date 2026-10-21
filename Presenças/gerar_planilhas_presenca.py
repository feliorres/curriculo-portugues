#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline de Processamento de Presenças - Google Meet History
Gera planilhas completas de presença em formato CSV para cada turma,
a partir dos arquivos de histórico do Google Meet.
"""

import os
import glob
import re
import csv
from collections import defaultdict
from datetime import datetime

# Diretório base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Pastas de entrada padrão
DEFAULT_INPUT_FOLDERS = [
    os.path.join(BASE_DIR, f"meetings-history ({i})")
    for i in range(59, 65)
]

# Diretório de saída para as planilhas geradas
OUTPUT_DIR = os.path.join(BASE_DIR, "Planilhas")

# Mapeamento oficial de código do Meet para o nome da Turma
MEET_CODE_TO_TURMA = {
    "izg-cssi-ndp": "5ºM1A-F",
    "wdz-nits-mda": "5ºM3A-F",
    "ijr-oszv-bvi": "5ºT2A-M",
    "azs-xgtk-jgx": "6ºM1A-F",
    "hri-padq-kjg": "6ºM4A-M",
    "uwf-ivjj-ctu": "6ºT2A-M",
    "hee-fwht-jzp": "7ºM3A-F",
    "ojq-kkdv-zdz": "7ºM4A-M",
    "kcz-jxdt-hsa": "8ºM1A-F",
    "izg-pswm-xwx": "8ºT2A-M",
    "amu-qbnt-dqy": "8ºT2A-M",
    "jzk-cwsn-bys": "9ºT1B-X",
    "mrb-sjaq-dwk": "9ºT2A-M",
}

# Códigos de reuniões que NÃO são turmas de alunos (ex.: reuniões pedagógicas)
NON_CLASS_CODES = {
    "eje-snxu-atk",  # Reunião Prof. Middle
    "rdo-mzzt-yvq",  # Reunião de Professores
}

# Usuários que não são alunos (professor, bots, coordenação, etc.)
IGNORE_USERS = {
    "felipe quintino torres",
    "read.ai meeting notes",
    "read.ai",
    "ângela kroetz dos santos",
    "angela kroetz dos santos",
}

# Normalizações específicas de nomes por turma (apelidos, emojis, contas de pais, variações de digitação)
CANONICAL_ALIASES = {
    # 5ºM1A-F
    "Evelin Louback": "Maria Sophia",
    "Viviane Monte De Melo": "Pietra Monte de Melo",
    "Viviane Monte de Melo": "Pietra Monte de Melo",
    "Heloísa": "Heloísa Vendrame",
    "heloísa": "Heloísa Vendrame",
    "heloisa": "Heloísa Vendrame",
    "Heloísa Maria": "Heloísa Vendrame",
    "HeloísaMaria": "Heloísa Vendrame",
    "Heloísa Vendrame": "Heloísa Vendrame",
    "Antonella pelet de carvalho": "Antonella Pelet de Carvalho",
    "Ãntonella Pelet de Carvalho": "Antonella Pelet de Carvalho",
    "antonela": "Antonella Pelet de Carvalho",
    "ana carolina de sa pelet": "Antonella Pelet de Carvalho",
    "Bella": "Bella Magalhães",
    "Maeia Sophia": "Maria Sophia",
    "Maruia Sophia": "Maria Sophia",
    "Carol Passos": "Luiza Passos",

    # 5ºM3A-F
    "Maria Isabel Bitencourt": "Maria Isabel Bitencourt Araujo",
    "Maria Isabel Bitencourt Bebel": "Maria Isabel Bitencourt Araujo",
    "Maria Isabel Bitencourt Araujo Bebel": "Maria Isabel Bitencourt Araujo",
    "Verena Coelho dos Santos": "Verena Coelho dos Santos",
    "Verena Coelho Dos Santos": "Verena Coelho dos Santos",
    "Valentina Bassegio": "Tina Bassegio",
    "Fabiana Foppa Bassegio": "Tina Bassegio",
    "Valentina": "Tina Bassegio",
    "wiliam carvalho": "Antonella Maria Carvalho",
    "Arthur Coelho Dos Santos": "Verena Coelho dos Santos",
    "Girlene Coelho": "Verena Coelho dos Santos",
    "LuBe Campana": "Emilly Blanco de Mello",

    # 5ºT2A-M
    "Mihael 10": "Mihael Torresani",
    "Mihael": "Mihael Torresani",
    "Samuel Henrique Rodrigues": "Samuel Henrique",
    "Pietro": "Pietro Friedrich Tiviroli",
    "Nicolas": "Nicolas Gregolato",
    "Adriele Gregolato": "Nicolas Gregolato",
    "Aline Neri Duarte": "Felipe Neri Duarte",
    "Elton Diêgo Bonifácio": "Theo Bonifácio",
    "Elton Diego Bonifácio": "Theo Bonifácio",
    "Familia Marques Bonifácio": "Theo Bonifácio",
    "Débora Abdalla": "Theo Bonifácio",

    # 6ºM1A-F
    "Maria Alice Teixeira": "Maria Alice da Silva Teixeira",
    "Maria Alice Da Silva Teixeira": "Maria Alice da Silva Teixeira",
    "sophie dousseau": "Sophie Dousseau",
    "Sofia Maria": "Sofia Maria",

    # 6ºM4A-M
    "Otavio Grava Maciel": "Otávio Grava Maciel",
    "Lucas Santos": "Lucas Santos Cunha",
    "lucas santos cunha": "Lucas Santos Cunha",
    "Lucas Santos Cunha": "Lucas Santos Cunha",
    "Andre Nardelli": "André Nardelli",
    "lu": "Lucas Santos Cunha",

    # 6ºT2A-M
    "Francisco": "Francisco Rolim Luís",
    "Fracisco": "Francisco Rolim Luís",
    "Francisco Rolim": "Francisco Rolim Luís",
    "Francisco Francisco Luís": "Francisco Rolim Luís",
    "Vanessa Rolim": "Francisco Rolim Luís",
    "Francisco Rolim Luís Português": "Francisco Rolim Luís",
    "Gabriel slonik": "Gabriel Slonik",
    "Luiz Carlos Slonik": "Gabriel Slonik",
    "Rafael Marques": "Rafael Marques Slonik",
    "Patrick Blanco": "Patrick Blanco Freitas",
    "Aliane Blanco": "Patrick Blanco Freitas",
    "Yasmin Blanco": "Patrick Blanco Freitas",
    "João Lucas da Silva Lima Silva Lima": "João Lucas",
    "PEDRO MACIEL": "Pedro Maciel",
    "victor": "Victor",
    "Arthur": "Arthur Soares Tenório",

    # 7ºM3A-F
    "Anastásia": "Anastásia Barbati",
    "Ana Luiza Andrade": "Ana Luiza Andrade",
    "ana luiza andrade": "Ana Luiza Andrade",
    "FERNANDA ANDRADE": "Fernanda Andrade",
    "Lorena Marnagoni": "Lorena Marangoni",
    "lorena marangoni": "Lorena Marangoni",
    "lorena padilha nascimento": "Lorena Padilha Nascimento",
    "heloisa padilha nascimento": "Heloisa Padilha Nascimento",
    "bianca padilha nascimento": "Bianca Padilha Nascimento",
    "marcio jose nascimento": "Lorena Padilha Nascimento",
    "Rubia Ferreira": "Rubia Ferreira",
    "RUBIA FERREIRA": "Rubia Ferreira",
    "RUBIAFERREIRA": "Rubia Ferreira",
    "RUBIA MARTINS": "Rubia Ferreira",
    "Talita Marangoni Neves": "Lorena Marangoni",
    "donatella brustolin": "Donatella Brustolin",
    "Sadi Jr Brustolin": "Donatella Brustolin",

    # 7ºM4A-M
    "antonio": "Antonio",
    "Gael": "Gael Joaquim Santini Vilela",
    "Gael Joaquim": "Gael Joaquim Santini Vilela",
    "Gustavo Mendes Martins.": "Gustavo Mendes Martins",
    "luis felipe": "Luis Felipe",
    "vitor sena": "Vitor Sena",
    "Priscila Sena": "Vitor Sena",
    "QUITERIA RIBEIRO": "Gabriel Costa Ribeiro",
    "Renan Ribeiro": "Gabriel Costa Ribeiro",
    "GABRIEL FOLLE PERES": "Gabriel Peres",

    # 8ºM1A-F
    "Clarice Soares Gonçalves Dona Maria 4": "Clarice Soares Gonçalves",
    "Srta Maria Clara Martins": "Maria Clara Martins",
    "Srta. Maria Clara Martins": "Maria Clara Martins",
    "Srta Marina Nogueira": "Marina Nogueira",
    "Srta. Marina Nogueira": "Marina Nogueira",
}


def clean_name(raw_name: str) -> str:
    """Limpa e normaliza o nome do participante."""
    # 1. Remove emojis
    cleaned = re.sub(
        r"[\U00010000-\U0010ffff\u2600-\u26ff\u2700-\u27bf\ufe00-\ufe0f]",
        "",
        raw_name,
    )
    # 2. Remove anotações entre colchetes e parênteses
    cleaned = re.sub(r"\[.*?\]", "", cleaned)
    cleaned = re.sub(r"\(.*?\)", "", cleaned)
    # 3. Remove pontuações e caracteres estranhos
    cleaned = re.sub(r"[^\w\sÀ-ÿ]", "", cleaned)
    # 4. Remove espaços extras
    cleaned = " ".join(cleaned.split()).strip()

    # 5. Normaliza capitalização se todo maiúsculo ou minúsculo
    if cleaned.islower() or cleaned.isupper():
        cleaned = cleaned.title()

    # 6. Verifica mapa canônico de apelidos/variações
    if raw_name in CANONICAL_ALIASES:
        return CANONICAL_ALIASES[raw_name]
    if cleaned in CANONICAL_ALIASES:
        return CANONICAL_ALIASES[cleaned]

    return cleaned


def parse_meeting_file(filepath: str):
    """
    Lê o cabeçalho e participantes de um arquivo de reunião do Google Meet.
    Retorna (meet_code, meet_title, date_iso, participants) ou None se inválido.
    """
    try:
        with open(filepath, "r", encoding="utf-8-sig", errors="ignore") as fp:
            first_lines = [fp.readline().strip().strip('"') for _ in range(6)]
    except Exception as e:
        print(f"Erro ao ler cabeçalho de {filepath}: {e}")
        return None

    meet_code = None
    meet_title = None
    created_on = None

    for line in first_lines:
        if "Meeting code:" in line:
            meet_code = line.split("Meeting code:", 1)[1].strip()
        elif "Meet:" in line:
            meet_title = line.split("Meet:", 1)[1].strip()
        elif "Created on" in line:
            created_on = line.split("Created on", 1)[1].strip()

    # Fallback para data a partir do nome do arquivo se necessário
    # Ex: meeting_05-10-2026_07-02-05_hee-fwht-jzp.csv
    date_iso = None
    if created_on:
        try:
            date_iso = created_on.split(" ")[0]
        except Exception:
            pass

    if not date_iso:
        basename = os.path.basename(filepath)
        match = re.search(r"meeting_(\d{2})-(\d{2})-(\d{4})", basename)
        if match:
            d, m, y = match.groups()
            date_iso = f"{y}-{m}-{d}"

    if not meet_code or not date_iso:
        return None

    # Lê os participantes
    participants = []
    try:
        with open(filepath, "r", encoding="utf-8-sig", errors="ignore") as fp:
            reader = csv.reader(fp)
            header_found = False
            for row in reader:
                if not row:
                    continue
                if row[0] == "Full Name":
                    header_found = True
                    continue
                if header_found and len(row) > 0:
                    raw_name = row[0].strip()
                    if not raw_name:
                        continue
                    if raw_name.lower() in IGNORE_USERS or "read.ai" in raw_name.lower():
                        continue
                    cleaned = clean_name(raw_name)
                    if cleaned:
                        participants.append(cleaned)
    except Exception as e:
        print(f"Erro ao ler participantes de {filepath}: {e}")

    return {
        "meet_code": meet_code,
        "meet_title": meet_title,
        "date_iso": date_iso,
        "participants": set(participants),
    }


def run_pipeline(input_folders=None, output_dir=None, start_date="2026-08-10"):
    """
    Executa a pipeline completa:
    1. Lê todos os arquivos CSV das pastas de entrada.
    2. Agrupa reuniões por turma.
    3. Filtra dias letivos a partir de start_date (10/08).
    4. Gera e salva as planilhas de presença em CSV.
    """
    if input_folders is None:
        input_folders = DEFAULT_INPUT_FOLDERS
    if output_dir is None:
        output_dir = OUTPUT_DIR

    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print("PIPELINE DE PRESENÇAS - GOOGLE MEET")
    print(f"Início das aulas considerado: {start_date}")
    print(f"Diretório de saída: {output_dir}")
    print("=" * 70)

    # Coleta todos os arquivos CSV
    all_files = []
    for folder in input_folders:
        if os.path.isdir(folder):
            files = glob.glob(os.path.join(folder, "*.csv"))
            all_files.extend(files)
            print(f"Pasta '{os.path.basename(folder)}': {len(files)} arquivos CSV encontrados.")
        else:
            print(f"Aviso: pasta não encontrada: {folder}")

    print(f"\nTotal de arquivos a processar: {len(all_files)}")

    # Estruturas de dados por turma
    # turma -> { "dates": set(date_iso), "attendance": defaultdict(set of dates), "students": set() }
    turma_data = defaultdict(lambda: {
        "dates": set(),
        "attendance": defaultdict(set),
        "students": set(),
        "meet_code": None,
        "meet_title": None,
    })

    processed_count = 0
    ignored_meetings = 0

    for filepath in all_files:
        meeting = parse_meeting_file(filepath)
        if not meeting:
            continue

        meet_code = meeting["meet_code"]
        date_iso = meeting["date_iso"]

        # Ignora reuniões não pedagógicas (de professores)
        if meet_code in NON_CLASS_CODES:
            ignored_meetings += 1
            continue

        # Filtra apenas a partir da data de início estipulada (10/08)
        if date_iso < start_date:
            continue

        # Identifica a turma
        turma_name = MEET_CODE_TO_TURMA.get(meet_code)
        if not turma_name:
            # Tenta extrair do título da reunião
            if meeting["meet_title"] and "Português" in meeting["meet_title"]:
                turma_name = meeting["meet_title"].replace("Português", "").strip().strip("- ")
            else:
                turma_name = meet_code

        # Se for a reunião curta de teste amu-qbnt-dqy (sem alunos), pula
        if meet_code == "amu-qbnt-dqy" and len(meeting["participants"]) == 0:
            continue

        t_entry = turma_data[turma_name]
        t_entry["meet_code"] = meet_code
        if meeting["meet_title"]:
            t_entry["meet_title"] = meeting["meet_title"]

        t_entry["dates"].add(date_iso)

        for student in meeting["participants"]:
            t_entry["students"].add(student)
            t_entry["attendance"][student].add(date_iso)

        processed_count += 1

    print(f"Arquivos processados com sucesso: {processed_count}")
    print(f"Reuniões de coordenação/não-turma ignoradas: {ignored_meetings}")
    print(f"Turmas identificadas: {len(turma_data)}\n")

    generated_files = []

    # Gera uma planilha CSV para cada turma
    for turma_name in sorted(turma_data.keys()):
        data = turma_data[turma_name]
        sorted_dates = sorted(list(data["dates"]))
        sorted_students = sorted(list(data["students"]))

        # Formata datas como DD/MM/AAAA para o cabeçalho
        date_headers = [
            datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m/%Y")
            for d in sorted_dates
        ]

        # Nome do arquivo CSV
        # Remove caracteres inválidos para sistema de arquivos se houver
        safe_turma_name = re.sub(r'[\\/*?:"<>|]', "", turma_name)
        csv_filename = f"{safe_turma_name}.csv"
        csv_filepath = os.path.join(output_dir, csv_filename)

        with open(csv_filepath, "w", encoding="utf-8-sig", newline="") as fp:
            writer = csv.writer(fp, delimiter=";")

            # Cabeçalho da planilha
            headers = ["Aluno"] + date_headers + ["Total Presenças", "Total Faltas", "% Presença"]
            writer.writerow(headers)

            # Linhas dos alunos
            for student in sorted_students:
                row = [student]
                presencas = 0
                faltas = 0

                for date_iso in sorted_dates:
                    if date_iso in data["attendance"][student]:
                        row.append("P")
                        presencas += 1
                    else:
                        row.append("F")
                        faltas += 1

                total_dias = len(sorted_dates)
                perc_presenca = (presencas / total_dias * 100) if total_dias > 0 else 0.0

                row.append(presencas)
                row.append(faltas)
                row.append(f"{perc_presenca:.1f}%")

                writer.writerow(row)

        generated_files.append((turma_name, csv_filepath, len(sorted_students), len(sorted_dates)))
        print(f"✓ Planilha gerada: {csv_filename} ({len(sorted_students)} alunos, {len(sorted_dates)} dias letivos)")

    print("\n" + "=" * 70)
    print("RESUMO DAS PLANILHAS GERADAS:")
    print("=" * 70)
    for turma_name, path, num_students, num_dates in generated_files:
        print(f"- {turma_name:12}: {num_students:2d} alunos | {num_dates:2d} dias letivos | {path}")

    return generated_files


if __name__ == "__main__":
    run_pipeline()
