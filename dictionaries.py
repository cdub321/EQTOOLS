
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
