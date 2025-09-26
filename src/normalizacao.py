from opentrons import protocol_api
import csv
import glob

metadata = {
    'protocolName': 'Diluição de Amostras de DNA',
    'author': 'Kailane',
    'description': 'Lê CSV, calcula a normalização e gera comandos de pipetagem.',
    'apiLevel': '2.15'
}

def run(protocol: protocol_api.ProtocolContext):
    # Importando Labware
    final_plate = protocol.load_labware('opentrons_96_wellplate_200ul_pcr_full_skirt', '1', 'Placa Final (96 poços)')
    dna_plate_1 = protocol.load_labware('opentrons_24_tuberack_nest_1.5ml_snapcap', '2', 'Placa de Amostras 1')
    dna_plate_2 = protocol.load_labware('opentrons_24_tuberack_nest_1.5ml_snapcap', '3', 'Placa de Amostras 2')
    dna_plate_3 = protocol.load_labware('opentrons_24_tuberack_nest_1.5ml_snapcap', '5', 'Placa de Amostras 3')
    dna_plate_4 = protocol.load_labware('opentrons_24_tuberack_nest_1.5ml_snapcap', '6', 'Placa de Amostras 4')
    water_reservoir = protocol.load_labware('usascientific_12_reservoir_22ml', '4', 'Reservatório de Água')
    tip_rack_1 = protocol.load_labware('opentrons_96_tiprack_300ul', '8')
    tip_rack_2 = protocol.load_labware('opentrons_96_tiprack_300ul', '9')
    
    p300 = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tip_rack_1, tip_rack_2])

    source_plates = {
        'dna_plate_1': dna_plate_1,
        'dna_plate_2': dna_plate_2,
        'dna_plate_3': dna_plate_3,
        'dna_plate_4': dna_plate_4,}
    
    source_water = water_reservoir.wells()[7]

    target_conc = 30.0  # ng/µL
    final_volume = 200  # µL
    output_data = []

    dilution_samples = []
    diluent_transfers = []
    dna_transfers = []

    # Importação de arquivo csv com inicio do nome QubitData...
    csv_path = glob.glob('/media/kai/2ccdf8b4-96af-4822-a501-d740f1a69bee/Protocolos_Opentrons/data/input/QubitData*.csv')
    
    if not csv_path:
        protocol.comment("Erro: Nenhum arquivo 'QubitData...' encontrado.")
        return
        
    csv_file_path = csv_path[0]
    protocol.comment(f"Arquivo CSV encontrado: {csv_file_path}")
    
    try:
        with open(csv_file_path, 'r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                sample_name = row.get('Sample Name')
                original_conc_str = row.get('Original Sample Conc.')
                if sample_name and original_conc_str:
                    try:
                        original_conc = float(original_conc_str)
                        dilution_samples.append({
                            'Sample Name': sample_name,
                            'Original Sample Conc.': original_conc
                        })
                    except (ValueError, TypeError):
                        protocol.comment(f"Amostra '{sample_name}' com concentração inválida: '{original_conc_str}'.")
    except FileNotFoundError:
        protocol.comment(f"Erro: Arquivo '{csv_file_path}' não encontrado.")
        return

    if not dilution_samples:
        protocol.comment("Nenhum dado válido encontrado no CSV.")
        return