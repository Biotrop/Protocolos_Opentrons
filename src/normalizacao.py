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

    """
    ----------------------------
        Mapeamento e Cálculo 
    ----------------------------
    """
    protocol.comment("Iniciando o cálculo dos volumes de diluição.")

    for i, sample in enumerate(dilution_samples):
        sample_name = sample['Sample Name']
        original_conc = sample['Original Sample Conc.']
        
        # Nome da amostra é SXX, sendo XX é o número
        sample_number_str = sample_name.strip().replace('S', '')
        if not sample_number_str.isdigit():
            protocol.comment(f"Ignorando amostra '{sample_name}': Formato de nome inválido.")
            continue
        
        sample_number = int(sample_number_str)
        
        if 1 <= sample_number <= 96 and original_conc > 0:
            # Poço de origem
            source_plate_index = (sample_number - 1) // 24
            source_well_index = (sample_number - 1) % 24
            
            source_plate = list(source_plates.values())[source_plate_index]
            source_well = source_plate.wells()[source_well_index]
            source_plate_name = list(source_plates.keys())[source_plate_index]
            
            # Poço de Destino
            rows_abcd = ['A', 'B', 'C', 'D']
            rows_efgh = ['E', 'F', 'G', 'H']

            # Mapeamento decidido
            if 1 <= sample_number <= 24:
                row = rows_efgh[(sample_number - 1) % 4]
                col = ((sample_number - 1) // 4) + 1
            elif 25 <= sample_number <= 48:
                row = rows_efgh[(sample_number - 25) % 4]
                col = ((sample_number - 25) // 4) + 7
            elif 49 <= sample_number <= 72:
                row = rows_abcd[(sample_number - 49) % 4]
                col = ((sample_number - 49) // 4) + 1
            elif 73 <= sample_number <= 96:
                row = rows_abcd[(sample_number - 73) % 4]
                col = ((sample_number - 73) // 4) + 7
            
            dest_well = final_plate.wells_by_name()[f"{row}{col}"]
            
            # Cálculo dos Volumes
            if original_conc >= target_conc:
                # Normalização: C1*V1 = C2*V2
                dna_volume = ((target_conc * final_volume) / original_conc)
                diluent_volume = (final_volume - dna_volume)
            else:
                # Concentração já abaixo: Transfere o volume final de DNA
                dna_volume = final_volume
                diluent_volume = 0

            dna_volume = round(dna_volume, 2)
            diluent_volume = round(diluent_volume, 2)
            
            # Garantir que os volumes sejam >= 1 µL para pipetagem eficiente
            #if diluent_volume < 1 and diluent_volume > 0:
            #    diluent_volume = 1.0
            #    dna_volume = final_volume - 1.0
            
            #if dna_volume < 1 and dna_volume > 0:
                # Se o volume de DNA é muito pequeno e precisa de diluente
            #    if diluent_volume > 0:
            #        protocol.comment(f"Amostra {sample_name}: Volume de DNA ({dna_volume:.2f} µL) muito pequeno para diluição. Ignorando a diluição, apenas transferindo DNA.")
            #        diluent_volume = 0
            #        dna_volume = final_volume
            #    else:
                    # Se não precisa de diluente, o volume total já é baixo ou não há diluição
            #        pass

            # Adiciona a listas de transferências de DNA e diluente
            if diluent_volume > 0:
                diluent_transfers.append({'volume': diluent_volume, 'destination': dest_well})
            if dna_volume > 0:
                dna_transfers.append({
                    'volume': dna_volume, 
                    'source': source_well,
                    'source_plate': source_plate_name,
                    'destination': dest_well
                })

            output_data.append({
                'Amostra': sample_name,
                'Volume DNA (µL)': dna_volume,
                'Poço Original DNA': source_well.display_name,
                'Slot Original DNA': source_plate_name,
                'Volume Diluente (µL)': diluent_volume,
                'Slot de Destino': 'final_plate',
                'Poço de Destino': dest_well.display_name
            })
        else:
            protocol.comment(f"Ignorando a amostra '{sample_name}': Número fora do intervalo (1-96) ou Conc. <= 0.")
         
    """
    ----------------------------
        Comandos de Pipetagem
    ----------------------------
    """
    
    # 1. Transferência de Diluente
    if diluent_transfers:
        protocol.comment("Iniciando a transferência de diluente (Água).")
        p300.pick_up_tip()
        
        for transfer in diluent_transfers:
            volume = transfer['volume']
            destination = transfer['destination']
            protocol.comment(f"Transferindo {volume} µL de diluente para {destination.display_name}.")
            p300.transfer(volume, source_water, destination, new_tip='never') 
        p300.drop_tip()


    # 2. Transferência de DNA 
    if dna_transfers:
        protocol.comment("Iniciando a transferência de DNA (Amostras).")
        
        for transfer in dna_transfers:
            volume = transfer['volume']
            source = transfer['source']
            destination = transfer['destination']
            
            p300.pick_up_tip()
            protocol.comment(f"Transferindo {volume} µL de DNA de {source.display_name} para {destination.display_name}.")

            p300.transfer(volume, source, destination, new_tip='never')
            p300.drop_tip()

    protocol.comment("Protocolo de diluição finalizado!")