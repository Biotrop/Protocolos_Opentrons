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