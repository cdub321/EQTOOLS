
from lookup_data import (
    tradeskill_lookup,
    container_lookup,
    race_lookup,
    class_lookup,
    deity_lookup,
    aa_category_lookup,
    aa_type_lookup,
    expansion_lookup,
    spell_effect_lookup,
)

TRADESKILL_IDS = dict(tradeskill_lookup)
CONTAINER_IDS = dict(container_lookup)

NPC_TYPES_COLUMNS = """
    npc_types.id, npc_types.name, npc_types.level,
    npc_types.race, npc_types.class, npc_types.bodytype, npc_types.hp, npc_types.mana,
    npc_types.gender, npc_types.texture, npc_types.helmtexture, npc_types.size,
    npc_types.loottable_id, npc_types.npc_spells_id, npc_types.npc_faction_id,
    npc_types.mindmg, npc_types.maxdmg, npc_types.npcspecialattks, npc_types.special_abilities,
    npc_types.MR, npc_types.CR, npc_types.DR, npc_types.FR, npc_types.PR, npc_types.AC,
    npc_types.attack_delay, npc_types.STR, npc_types.STA, npc_types.DEX,
    npc_types.AGI, npc_types._INT, npc_types.WIS, npc_types.maxlevel, npc_types.skip_global_loot, npc_types.exp_mod
"""

RACE_OPTIONS = {
    data['name']: data['bit_value'] for _, data in sorted(race_lookup.items())
}

CLASS_OPTIONS = {
    data['name']: data['bit_value'] for _, data in sorted(class_lookup.items())
}

DEITY_OPTIONS = {
    data['name']: data['bit_value'] for _, data in sorted(deity_lookup.items())
}

CATEGORY_OPTIONS = [
    (entry['value'], entry['label']) for entry in aa_category_lookup
]

TYPE_OPTIONS = [
    (entry['value'], entry['label']) for entry in aa_type_lookup
]

EXPANSION_OPTIONS = [
    (entry['value'], entry['label']) for entry in expansion_lookup
]

SPELL_EFFECTS = dict(sorted(spell_effect_lookup.items()))

CLASS_BITMASK_DISPLAY = {
    data['bit_value']: data['abbr'] for data in class_lookup.values()
}
CLASS_BITMASK_DISPLAY[65535] = "ALL"

RACE_BITMASK_DISPLAY = {
    data['bit_value']: data['abbr'] for data in race_lookup.values()
}
RACE_BITMASK_DISPLAY[65535] = "ALL"

SLOT_BITMASK_DISPLAY = {
    1: "Charm", 2: "Ear", 4: "Head", 8: "Face",
    16: "Ear", 32: "Neck", 64: "Shoulder", 128: "Arms",
    256: "Back", 512: "Bracer", 1024: "Bracer", 2048: "Range",
    4096: "Hands", 8192: "Primary", 16384: "Secondary",
    32768: "Ring", 65536: "Ring", 131072: "Chest",
    262144: "Legs", 524288: "Feet", 1048576: "Waist",
    2097152: "Powersource", 4194304: "Ammo"
}

# Item stat display configuration for image overlay
# This preserves the exact pixel positioning from the loot tools item display
ITEM_STAT_DISPLAY_CONFIG = {
    # Fixed positions for header information
    "header_positions": {
        "Name": {
            "x": 150, "y": 5, 
            "color": "white", 
            "font": ("Arial", 10),
            "label": None  # No label for Name
        },
        "classes": {
            "x": 55, "y": 44, 
            "color": "skyblue", 
            "font": ("Arial", 9),
            "label": "Class"  # Singular form
        },
        "races": {
            "x": 55, "y": 57, 
            "color": "skyblue", 
            "font": ("Arial", 9),
            "label": "Race"
        },
        "slots": {
            "x": 55, "y": 70, 
            "color": "skyblue", 
            "font": ("Arial", 9),
        }, 
    },
    
    # Special properties displayed in a horizontal row
    "property_row": {
        "y": 30,
        "base_x": 55,
        "spacing": 40,
        "properties": {
            "magic": {
                "color": "white", 
                "font": ("Arial", 9),
                "format": lambda value: "Magic" if value == 1 else ""
            },
            "loregroup": {
                "color": "white", 
                "font": ("Arial", 9),
                "format": lambda value: " Lore" if value == -1 else ""
            },
            "nodrop": {
                "color": "white", 
                "font": ("Arial", 9),
                "format": lambda value: "No Drop " if value == 0 else ""
            },
            "fvnodrop": {
                "color": "white", 
                "font": ("Arial", 9),
                "format": lambda value: "   FV No Drop" if value == 1 else ""
            },
            "norent": {
                "color": "white", 
                "font": ("Arial", 9),
                "format": lambda value: "No Rent" if value == 0 else ""
            },
            "attuneable": {
                "color": "white", 
                "font": ("Arial", 9),
                "format": lambda value: "Attune" if value == 1 else ""
            }
        }
    },
    
    # Multi-column stat layout (5 columns)
    "stat_columns": [
        {# First Column - Primary Stats
            "stats": [
                {"name": "astr", "label": "STR", "color": "white"},
                {"name": "asta", "label": "STA", "color": "white"},
                {"name": "adex", "label": "DEX", "color": "white"},
                {"name": "aagi", "label": "AGI", "color": "white"},
                {"name": "aint", "label": "INT", "color": "white"},
                {"name": "awis", "label": "WIS", "color": "white"},
                {"name": "acha", "label": "CHA", "color": "white"},
            ],
            "heroic_stats": [
                {"name": "heroic_str", "label": "STR", "color": "gold"},
                {"name": "heroic_sta", "label": "STA", "color": "gold"},
                {"name": "heroic_dex", "label": "DEX", "color": "gold"},
                {"name": "heroic_agi", "label": "AGI", "color": "gold"},
                {"name": "heroic_int", "label": "INT", "color": "gold"},
                {"name": "heroic_wis", "label": "WIS", "color": "gold"},
                {"name": "heroic_cha", "label": "CHA", "color": "gold"},
            ],
            "x": 5,  # Starting X position for the first column
            "y": 85,  # Starting Y position for the first column
            "spacing": 13,  # Vertical spacing between stats
        },
        
        {# Second Column - Health/Mana/Regen
            "stats": [
                {"name": "ac", "label": "AC", "color": "white"},
                {"name": "hp", "label": "HP", "color": "white"},
                {"name": "mana", "label": "Mana", "color": "white"},
                {"name": "endur", "label": "Endur", "color": "white"},
                {"name": "regen", "label": "HP Regen", "color": "white"},
                {"name": "manaregen", "label": "Mana Regen", "color": "white"},
                {"name": "enduranceregen", "label": "Endur. Regen", "color": "white"},
            ],
            "x": 74, "y": 85, "spacing": 13,
        },
        
        {# Third Column - Resistances
            "stats": [
                {"name": "mr", "label": "MR", "color": "white"},
                {"name": "cr", "label": "CR", "color": "white"},
                {"name": "fr", "label": "FR", "color": "white"},
                {"name": "dr", "label": "DR", "color": "white"},
                {"name": "pr", "label": "PR", "color": "white"},
                {"name": "svcorruption", "label": "PR", "color": "white"},
            ],
            "heroicstats": [
                {"name": "heroic_mr", "label": "MR", "color": "white"},
                {"name": "heroic_cr", "label": "CR", "color": "white"},
                {"name": "heroic_fr", "label": "FR", "color": "white"},
                {"name": "heroic_dr", "label": "DR", "color": "white"},
                {"name": "heroic_pr", "label": "PR", "color": "white"},
                {"name": "heroic_svcorrup", "label": "PR", "color": "white"},
            ],
            "x": 150, "y": 85, "spacing": 13,  
        },
        
        {# Fourth Column - Combat Stats
            "stats": [
                {"name": "shielding", "label": "Shielding", "color": "white"},
                {"name": "strikethrough", "label": "StrikeThru", "color": "white"},
                {"name": "damageshield", "label": "DmgShield", "color": "white"},
                {"name": "dotshielding", "label": "DoT Shield", "color": "white"},
                {"name": "accuracy", "label": "Accuracy", "color": "white"},
                {"name": "avoidance", "label": "Avoidance", "color": "white"},
                {"name": "spellshield", "label": "Spell Shield", "color": "white"},
                {"name": "stunresist", "label": "Stun Shield", "color": "white"},
            ],
            "x": 210, "y": 85, "spacing": 13,  
        },
        
        {# Fifth Column - Weapon Stats
            "stats": [
                {"name": "damage", "label": "Damage", "color": "white"},
                {"name": "delay", "label": "Delay", "color": "white"},
                {"name": "range", "label": "Range", "color": "white"},
                {"name": "regen", "label": "HP Regen", "color": "white"},
                {"name": "attack", "label": "Attk", "color": "white"},
                {"name": "avoidance", "label": "Avoidance", "color": "white"},
                {"name": "spellshield", "label": "Spell Shield", "color": "white"},
                {"name": "haste", "label": "Haste", "color": "white"},
            ],
            "x": 295, "y": 85, "spacing": 13,
        },
    ],
    
    # Icon positioning
    "icon_position": {
        "x": 28,
        "y": 57
    }
}

SPECIAL_ABILITIES = [
    (1, "Summon", [("Type (1=To NPC, 2=To Target)", "1"), ("Cooldown ms", "6000"), ("HP% before summon", "97")]),
    (2, "Enrage", [("Enabled (1/0)", "1"), ("HP% to Enrage", ""), ("Duration ms", "10000"), ("Cooldown ms", "360000")]),
    (3, "Rampage", [("Enabled (1/0)", "1"), ("Proc chance", "20"), ("Target count", ""), ("Flat dmg", ""), ("Ignore % armor", ""), ("Ignore flat armor", ""), ("% NPC Crit against", "100"), ("Flat crit bonus", "")]),
    (4, "AE Rampage", [("Enabled (1/0)", "1"), ("Target count", ""), ("% of normal dmg", "100"), ("Flat dmg bonus", ""), ("Ignore % armor", ""), ("Ignore flat armor", ""), ("% NPC Crit against", "100"), ("Flat crit bonus", "")]),
    (5, "Flurry", [("Enabled (1/0)", "1"), ("Flurry count", ""), ("% of normal dmg", "100"), ("Flat dmg bonus", ""), ("Ignore % armor", ""), ("Ignore flat armor", ""), ("% NPC Crit", "100"), ("Flat crit bonus", "")]),
    (6, "Triple Attack", []),
    (7, "Quad Attack", []),
    (8, "Dual Wield", []),
    (9, "Bane Attack", []),
    (10, "Magic Attack", []),
    (11, "Ranged Attack", [("Attack count", "0"), ("Max Range", "250"), ("Percent Hit Chance Modifier", "0"), ("Percent Damage Modifier", "0"), ("Min Range", "25")]),
    (12, "Unslowable", []),
    (13, "Unmezable", []),
    (14, "Uncharmable", []),
    (15, "Unstunnable", []),
    (16, "Unsnareable", []),
    (17, "Unfearable", []),
    (18, "Immune to Dispell", []),
    (19, "Immune to Melee", []),
    (20, "Immune to Magic", []),
    (21, "Immune to Fleeing", []),
    (22, "Immune to Non-Bane Melee", []),
    (23, "Immune to Non-Magical Melee", []),
    (24, "Will Not Aggro", []),
    (25, "Immune to Aggro", []),
    (26, "Resist Ranged Spells", []),
    (27, "See through Feign Death", []),
    (28, "Immune to Taunt", []),
    (29, "Tunnel Vision", [("Aggro modifier on non-tanks", "75")]),
    (30, "Does NOT buff/heal friends", []),
    (31, "Unpacifiable", []),
    (32, "Leashed", [("Leash range", "0")]),
    (33, "Tethered", [("Aggro Range", "0")]),
    (34, "Destructible Object", []),
    (35, "No Harm from Players", []),
    (36, "Always Flee", []),
    (37, "Flee Percent", [("Flee at % HP", "0"), ("% chance to flee", "0")]),
    (38, "Allow Beneficial", []),
    (39, "Disable Melee", []),
    (40, "Chase Distance", [("Max chase distance", "0"), ("Min chase distance", "0"), ("Ignore LOS", "0")]),
    (41, "Allow Tank", [("Enabled (1/0)", "1")]),
    (42, "Ignore Root Aggro", []),
    (43, "Casting Resist Diff", [("Resist difference", "0")]),
    (44, "Counter Avoid Damage", [("% Reduction (Riposte, Parry, Block, Dodge)", "0"), ("% Riposte", "0"), ("% Block", "0"), ("% Parry", "0"), ("% Dodge", "0")]),
    (45, "Proximity Aggro", []),
    (46, "Immune to Ranged Attacks", []),
    (47, "Immune to Client Damage", []),
    (48, "Immune to NPC Damage", []),
    (49, "Immune to Client Aggro", []),
    (50, "Immune to NPC Aggro", []),
    (51, "Modify Avoid Damage", [("% Addition (Riposte, Parry, Block, Dodge)", "0"), ("% Riposte", "0"), ("% Parry", "0"), ("% Block", "0"), ("% Dodge", "0")]),
    (52, "Immune to Memory Fades", []),
    (53, "Immune to Open", []),
    (54, "Immune to Assassinate", []),
    (55, "Immune to Headshot", []),
    (56, "Immune to Bot Aggro", []),
    (57, "Immune to Bot Damage", []),
]
