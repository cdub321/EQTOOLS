import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import glob
from PIL import Image, ImageTk
from mysql.connector import Error

# Allow running this module standalone by adding parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SPECIAL_ABILITIES_FIELD_TUPLES = [
    ("sa_summon", "Summon", "check", {"fullrow": True}),
    ("sa_summon_p1", "Type (1=To NPC, 2=To Target)", "text", {"default": "1", "width": 8}),
    ("sa_summon_p2", "Cooldown ms", "text", {"default": "6000", "width": 8}),
    ("sa_summon_p3", "HP% before summon", "text", {"default": "97", "width": 8}),
    ("sa_enrage", "Enrage", "check", {"fullrow": True}),
    ("sa_enrage_p1", "HP% to Enrage", "text", {"default": "", "width": 8}),
    ("sa_enrage_p2", "Duration ms", "text", {"default": "10000", "width": 8}),
    ("sa_enrage_p3", "Cooldown ms", "text", {"default": "360000", "width": 8}),
    ("sa_rampage", "Rampage", "check", {"fullrow": True}),
    ("sa_rampage_p1", "Proc chance", "text", {"default": "20", "width": 8}),
    ("sa_rampage_p2", "Target count", "text", {"default": "", "width": 8}),
    ("sa_rampage_p3", "Flat dmg", "text", {"default": "", "width": 8}),
    ("sa_rampage_p4", "Ignore % armor", "text", {"default": "", "width": 8}),
    ("sa_rampage_p5", "Ignore flat armor", "text", {"default": "", "width": 8}),
    ("sa_rampage_p6", "% NPC Crit against", "text", {"default": "100", "width": 8}),
    ("sa_rampage_p7", "Flat crit bonus", "text", {"default": "", "width": 8}),
    ("sa_ae_rampage", "AE Rampage", "check", {"fullrow": True}),
    ("sa_ae_rampage_p1", "Target count", "text", {"default": "", "width": 8}),
    ("sa_ae_rampage_p2", "% of normal dmg", "text", {"default": "100", "width": 8}),
    ("sa_ae_rampage_p3", "Flat dmg bonus", "text", {"default": "", "width": 8}),
    ("sa_ae_rampage_p4", "Ignore % armor", "text", {"default": "", "width": 8}),
    ("sa_ae_rampage_p5", "Ignore flat armor", "text", {"default": "", "width": 8}),
    ("sa_ae_rampage_p6", "% NPC Crit against", "text", {"default": "100", "width": 8}),
    ("sa_ae_rampage_p7", "Flat crit bonus", "text", {"default": "", "width": 8}),
    ("sa_flurry", "Flurry", "check", {"fullrow": True}),
    ("sa_flurry_p1", "Flurry count", "text", {"default": "", "width": 8}),
    ("sa_flurry_p2", "% of normal dmg", "text", {"default": "100", "width": 8}),
    ("sa_flurry_p3", "Flat dmg bonus", "text", {"default": "", "width": 8}),
    ("sa_flurry_p4", "Ignore % armor", "text", {"default": "", "width": 8}),
    ("sa_flurry_p5", "Ignore flat armor", "text", {"default": "", "width": 8}),
    ("sa_flurry_p6", "% NPC Crit", "text", {"default": "100", "width": 8}),
    ("sa_flurry_p7", "Flat crit bonus", "text", {"default": "", "width": 8}),
    ("sa_tunnel_vision", "Tunnel Vision", "check", {"fullrow": True}),
    ("sa_tunnel_vision_p1", "Aggro modifier on non-tanks", "text", {"default": "75", "width": 8}),
    ("sa_unmezable", "Unmezable", "check", {"fullrow": True}),
    ("sa_quad_attack", "Quad Attack", "check", {"fullrow": True}),
    ("sa_leashed", "Leashed", "check", {"fullrow": True}),
    ("sa_leashed_p1", "Leash range", "text", {"default": "0", "width": 8}),
    ("sa_triple_attack", "Triple Attack", "check", {"fullrow": True}),
    ("sa_dual_wield", "Dual Wield", "check", {"fullrow": True}),
    ("sa_tethered", "Tethered", "check", {"fullrow": True}),
    ("sa_tethered_p1", "Aggro Range", "text", {"default": "0", "width": 8}),
    ("sa_bane_attack", "Bane Attack", "check", {"fullrow": True}),
    ("sa_magic_attack", "Magic Attack", "check", {"fullrow": True}),
    ("sa_casting_resist_diff", "Casting Resist Diff", "check", {"fullrow": True}),
    ("sa_casting_resist_diff_p1", "Resist difference", "text", {"default": "0", "width": 8}),
    ("sa_uncharmable", "Uncharmable", "check", {"fullrow": True}),
    ("sa_unstunnable", "Unstunnable", "check", {"fullrow": True}),
    ("sa_chase_distance", "Chase Distance", "check", {"fullrow": True}),
    ("sa_chase_distance_p1", "Max chase distance", "text", {"default": "0", "width": 8}),
    ("sa_chase_distance_p2", "Min chase distance", "text", {"default": "0", "width": 8}),
    ("sa_chase_distance_p3", "Ignore LOS", "text", {"default": "0", "width": 8}),
    ("sa_always_flee", "Always Flee", "check", {"fullrow": True}),
    ("sa_flee_percent", "Flee Percent", "check", {"fullrow": True}),
    ("sa_flee_percent_p1", "Flee at % HP", "text", {"default": "0", "width": 8}),
    ("sa_flee_percent_p2", "% chance to flee", "text", {"default": "0", "width": 8}),
    ("sa_counter_avoid_damage", "Counter Avoid Damage", "check", {"fullrow": True}),
    ("sa_counter_avoid_damage_p1", "% Reduction (Riposte, Parry, Block, Dodge)", "text", {"default": "0", "width": 8}),
    ("sa_counter_avoid_damage_p2", "% Riposte", "text", {"default": "0", "width": 8}),
    ("sa_counter_avoid_damage_p3", "% Block", "text", {"default": "0", "width": 8}),
    ("sa_counter_avoid_damage_p4", "% Parry", "text", {"default": "0", "width": 8}),
    ("sa_counter_avoid_damage_p5", "% Dodge", "text", {"default": "0", "width": 8}),
    ("sa_allow_beneficial", "Allow Beneficial", "check", {"fullrow": True}),
    ("sa_ranged_attack", "Ranged Attack", "check", {"fullrow": True}),
    ("sa_ranged_attack_p1", "Attack count", "text", {"default": "0", "width": 8}),
    ("sa_ranged_attack_p2", "Max Range", "text", {"default": "250", "width": 8}),
    ("sa_ranged_attack_p3", "Percent Hit Chance Modifier", "text", {"default": "0", "width": 8}),
    ("sa_ranged_attack_p4", "Percent Damage Modifier", "text", {"default": "0", "width": 8}),
    ("sa_ranged_attack_p5", "Min Range", "text", {"default": "25", "width": 8}),
    ("sa_unslowable", "Unslowable", "check", {"fullrow": True}),

    
    ("sa_unsnareable", "Unsnareable", "check", {"fullrow": True}),
    ("sa_unfearable", "Unfearable", "check", {"fullrow": True}),
    ("sa_immune_to_dispell", "Immune to Dispell", "check", {"fullrow": True}),
    ("sa_immune_to_melee", "Immune to Melee", "check", {"fullrow": True}),
    ("sa_immune_to_magic", "Immune to Magic", "check", {"fullrow": True}),
    ("sa_immune_to_fleeing", "Immune to Fleeing", "check", {"fullrow": True}),
    ("sa_immune_to_non_bane_melee", "Immune to Non-Bane Melee", "check", {"fullrow": True}),
    ("sa_immune_to_non_magical_melee", "Immune to Non-Magical Melee", "check", {"fullrow": True}),
    ("sa_will_not_aggro", "Will Not Aggro", "check", {"fullrow": True}),
    ("sa_immune_to_aggro", "Immune to Aggro", "check", {"fullrow": True}),
    ("sa_resist_ranged_spells", "Resist Ranged Spells", "check", {"fullrow": True}),
    ("sa_see_through_feign_death", "See through Feign Death", "check", {"fullrow": True}),
    ("sa_immune_to_taunt", "Immune to Taunt", "check", {"fullrow": True}),

    ("sa_does_not_buff_heal_friends", "Does NOT buff/heal friends", "check", {"fullrow": True}),
    ("sa_unpacifiable", "Unpacifiable", "check", {"fullrow": True}),


    ("sa_destructible_object", "Destructible Object", "check", {"fullrow": True}),
    ("sa_no_harm_from_players", "No Harm from Players", "check", {"fullrow": True}),
    
    ("sa_disable_melee", "Disable Melee", "check", {"fullrow": True}),
    
    ("sa_allow_tank", "Allow Tank", "check", {"fullrow": True}),
    ("sa_ignore_root_aggro", "Ignore Root Aggro", "check", {"fullrow": True}),
    
    
    ("sa_proximity_aggro", "Proximity Aggro", "check", {"fullrow": True}),
    ("sa_immune_to_ranged_attacks", "Immune to Ranged Attacks", "check", {"fullrow": True}),
    ("sa_immune_to_client_damage", "Immune to Client Damage", "check", {"fullrow": True}),
    ("sa_immune_to_npc_damage", "Immune to NPC Damage", "check", {"fullrow": True}),
    ("sa_immune_to_client_aggro", "Immune to Client Aggro", "check", {"fullrow": True}),
    ("sa_immune_to_npc_aggro", "Immune to NPC Aggro", "check", {"fullrow": True}),
    ("sa_modify_avoid_damage", "Modify Avoid Damage", "check", {"fullrow": True}),
    ("sa_modify_avoid_damage_p1", "% Addition (Riposte, Parry, Block, Dodge)", "text", {"default": "0", "width": 8}),
    ("sa_modify_avoid_damage_p2", "% Riposte", "text", {"default": "0", "width": 8}),
    ("sa_modify_avoid_damage_p3", "% Parry", "text", {"default": "0", "width": 8}),
    ("sa_modify_avoid_damage_p4", "% Block", "text", {"default": "0", "width": 8}),
    ("sa_modify_avoid_damage_p5", "% Dodge", "text", {"default": "0", "width": 8}),
    ("sa_immune_to_memory_fades", "Immune to Memory Fades", "check", {"fullrow": True}),
    ("sa_immune_to_open", "Immune to Open", "check", {"fullrow": True}),
    ("sa_immune_to_assassinate", "Immune to Assassinate", "check", {"fullrow": True}),
    ("sa_immune_to_headshot", "Immune to Headshot", "check", {"fullrow": True}),
    ("sa_immune_to_bot_aggro", "Immune to Bot Aggro", "check", {"fullrow": True}),
    ("sa_immune_to_bot_damage", "Immune to Bot Damage", "check", {"fullrow": True}),
]

SPECIAL_ABILITY_SPECS = [
    {"id": 1, "enable_key": "sa_summon", "param_keys": [("sa_summon_p1", "1"), ("sa_summon_p2", "6000"), ("sa_summon_p3", "97")]},
    {"id": 2, "enable_key": "sa_enrage", "param_keys": [("sa_enrage_p1", ""), ("sa_enrage_p2", "10000"), ("sa_enrage_p3", "360000")]},
    {"id": 3, "enable_key": "sa_rampage", "param_keys": [("sa_rampage_p1", "20"), ("sa_rampage_p2", ""), ("sa_rampage_p3", ""), ("sa_rampage_p4", ""), ("sa_rampage_p5", ""), ("sa_rampage_p6", "100"), ("sa_rampage_p7", "")]},
    {"id": 4, "enable_key": "sa_ae_rampage", "param_keys": [("sa_ae_rampage_p1", ""), ("sa_ae_rampage_p2", "100"), ("sa_ae_rampage_p3", ""), ("sa_ae_rampage_p4", ""), ("sa_ae_rampage_p5", ""), ("sa_ae_rampage_p6", "100"), ("sa_ae_rampage_p7", "")]},
    {"id": 5, "enable_key": "sa_flurry", "param_keys": [("sa_flurry_p1", ""), ("sa_flurry_p2", "100"), ("sa_flurry_p3", ""), ("sa_flurry_p4", ""), ("sa_flurry_p5", ""), ("sa_flurry_p6", "100"), ("sa_flurry_p7", "")]},
    {"id": 6, "enable_key": "sa_triple_attack", "param_keys": []},
    {"id": 7, "enable_key": "sa_quad_attack", "param_keys": []},
    {"id": 8, "enable_key": "sa_dual_wield", "param_keys": []},
    {"id": 9, "enable_key": "sa_bane_attack", "param_keys": []},
    {"id": 10, "enable_key": "sa_magic_attack", "param_keys": []},
    {"id": 11, "enable_key": "sa_ranged_attack", "param_keys": [("sa_ranged_attack_p1", "0"), ("sa_ranged_attack_p2", "250"), ("sa_ranged_attack_p3", "0"), ("sa_ranged_attack_p4", "0"), ("sa_ranged_attack_p5", "25")]},
    {"id": 12, "enable_key": "sa_unslowable", "param_keys": []},
    {"id": 13, "enable_key": "sa_unmezable", "param_keys": []},
    {"id": 14, "enable_key": "sa_uncharmable", "param_keys": []},
    {"id": 15, "enable_key": "sa_unstunnable", "param_keys": []},
    {"id": 16, "enable_key": "sa_unsnareable", "param_keys": []},
    {"id": 17, "enable_key": "sa_unfearable", "param_keys": []},
    {"id": 18, "enable_key": "sa_immune_to_dispell", "param_keys": []},
    {"id": 19, "enable_key": "sa_immune_to_melee", "param_keys": []},
    {"id": 20, "enable_key": "sa_immune_to_magic", "param_keys": []},
    {"id": 21, "enable_key": "sa_immune_to_fleeing", "param_keys": []},
    {"id": 22, "enable_key": "sa_immune_to_non_bane_melee", "param_keys": []},
    {"id": 23, "enable_key": "sa_immune_to_non_magical_melee", "param_keys": []},
    {"id": 24, "enable_key": "sa_will_not_aggro", "param_keys": []},
    {"id": 25, "enable_key": "sa_immune_to_aggro", "param_keys": []},
    {"id": 26, "enable_key": "sa_resist_ranged_spells", "param_keys": []},
    {"id": 27, "enable_key": "sa_see_through_feign_death", "param_keys": []},
    {"id": 28, "enable_key": "sa_immune_to_taunt", "param_keys": []},
    {"id": 29, "enable_key": "sa_tunnel_vision", "param_keys": [("sa_tunnel_vision_p1", "75")]},
    {"id": 30, "enable_key": "sa_does_not_buff_heal_friends", "param_keys": []},
    {"id": 31, "enable_key": "sa_unpacifiable", "param_keys": []},
    {"id": 32, "enable_key": "sa_leashed", "param_keys": [("sa_leashed_p1", "0")]},
    {"id": 33, "enable_key": "sa_tethered", "param_keys": [("sa_tethered_p1", "0")]},
    {"id": 34, "enable_key": "sa_destructible_object", "param_keys": []},
    {"id": 35, "enable_key": "sa_no_harm_from_players", "param_keys": []},
    {"id": 36, "enable_key": "sa_always_flee", "param_keys": []},
    {"id": 37, "enable_key": "sa_flee_percent", "param_keys": [("sa_flee_percent_p1", "0"), ("sa_flee_percent_p2", "0")]},
    {"id": 38, "enable_key": "sa_allow_beneficial", "param_keys": []},
    {"id": 39, "enable_key": "sa_disable_melee", "param_keys": []},
    {"id": 40, "enable_key": "sa_chase_distance", "param_keys": [("sa_chase_distance_p1", "0"), ("sa_chase_distance_p2", "0"), ("sa_chase_distance_p3", "0")]},
    {"id": 41, "enable_key": "sa_allow_tank", "param_keys": []},
    {"id": 42, "enable_key": "sa_ignore_root_aggro", "param_keys": []},
    {"id": 43, "enable_key": "sa_casting_resist_diff", "param_keys": [("sa_casting_resist_diff_p1", "0")]},
    {"id": 44, "enable_key": "sa_counter_avoid_damage", "param_keys": [("sa_counter_avoid_damage_p1", "0"), ("sa_counter_avoid_damage_p2", "0"), ("sa_counter_avoid_damage_p3", "0"), ("sa_counter_avoid_damage_p4", "0"), ("sa_counter_avoid_damage_p5", "0")]},
    {"id": 45, "enable_key": "sa_proximity_aggro", "param_keys": []},
    {"id": 46, "enable_key": "sa_immune_to_ranged_attacks", "param_keys": []},
    {"id": 47, "enable_key": "sa_immune_to_client_damage", "param_keys": []},
    {"id": 48, "enable_key": "sa_immune_to_npc_damage", "param_keys": []},
    {"id": 49, "enable_key": "sa_immune_to_client_aggro", "param_keys": []},
    {"id": 50, "enable_key": "sa_immune_to_npc_aggro", "param_keys": []},
    {"id": 51, "enable_key": "sa_modify_avoid_damage", "param_keys": [("sa_modify_avoid_damage_p1", "0"), ("sa_modify_avoid_damage_p2", "0"), ("sa_modify_avoid_damage_p3", "0"), ("sa_modify_avoid_damage_p4", "0"), ("sa_modify_avoid_damage_p5", "0")]},
    {"id": 52, "enable_key": "sa_immune_to_memory_fades", "param_keys": []},
    {"id": 53, "enable_key": "sa_immune_to_open", "param_keys": []},
    {"id": 54, "enable_key": "sa_immune_to_assassinate", "param_keys": []},
    {"id": 55, "enable_key": "sa_immune_to_headshot", "param_keys": []},
    {"id": 56, "enable_key": "sa_immune_to_bot_aggro", "param_keys": []},
    {"id": 57, "enable_key": "sa_immune_to_bot_damage", "param_keys": []},
]


LOOKUP_CONFIG = {
    "npc_spells_id": {
        "title": "Select NPC Spells",
        "columns": [("id", "ID"), ("name", "Name")],
        "type": "npc_spells",
    },
    "npc_spells_effects_id": {
        "title": "Select NPC Spell Effects",
        "columns": [("id", "ID"), ("name", "Name")],
        "type": "npc_spells_effects",
    },
    "merchant_id": {
        "title": "Select Merchant",
        "columns": [("id", "Merchant ID"), ("items", "Items"), ("sample_items", "Sample Items")],
        "type": "merchant",
    },
}

COMBAT_DROPDOWN_PRESETS = {
    "attack_count": ["", "1", "2", "3", "4", "5", "6"],
    "attack_speed": ["", "-100", "-50", "-25", "0", "10", "25", "50", "75", "100"],
    "attack_delay": ["", "10", "12", "18", "20", "24", "30", "35", "40", "45", "50"],
    "Accuracy": ["", "0", "25", "50", "75", "100", "150", "200"],
    "Avoidance": ["", "0", "25", "50", "75", "100", "150", "200"],
    "slow_mitigation": ["", "0", "10", "25", "50", "75", "90", "100"],
    "aggroradius": ["", "35", "50", "75", "100", "125", "150", "200"],
    "assistradius": ["", "35", "50", "75", "100", "125", "150", "200"],
}

ENTRY_FIELD_SECTIONS = [
    ("General", 6, [
        ("id", "ID", "text"), ("class", "Class", "text"), ("texture", "Texture", "text", {"width": 6}), ("npc_spells_id", "NPC Spells ID", "text"), ("loottable_id", "Loottable ID", "text"), ("stuck_behavior", "Stuck Behavior", "text"),
        ("name", "Name", "text", {"width": 20}), ("race", "Race", "text"), ("helmtexture", "Helm", "text", {"width": 6}), ("merchant_id", "Merchant ID", "text"), ("flymode", "Flymode", "text"), 
        ("lastname", "Surname", "text", {"width": 16}), ("gender", "Gender", "text", {"width": 6}), ("size", "Size", "text", {"width": 6}), ("npc_faction_id", "NPC Faction ID", "text"), ("emoteid", "Emote ID", "text"), ("exp_mod", "Exp Mod", "text"),
        ("level", "Level", "text"), ("bodytype", "Bodytype", "text"), ("model", "Model", "text", {"width": 8}), ("faction_amount", "Faction Amount", "text"), ("light", "Light", "text", {"width": 6}), ("walkspeed", "Walkspeed", "text"),
        ("greed", "Greed", "text"), ("runspeed", "Runspeed", "text"), ("raid_target", "Raid Target", "check"), ("show_name", "Show Name", "check"), ("keeps_sold_items", "Keeps Sold Items", "check"), ("is_parcel_merchant", "Parcel Merchant", "check"),
        ("trackable", "Trackable", "check"), ("findable", "Findable", "check"), ("untargetable", "Untargetable", "check"), ("underwater", "Underwater", "check"),
        ("no_target_hotkey", "No Target Hotkey", "check"), ("skip_global_loot", "Skip Global Loot", "check"), ("multiquest_enabled", "Multiquest Enabled", "check"),

    ]),
    ("Stats", 7, [
        ("AC", "AC", "text", {"width": 6}), ("hp", "HP", "text", {"width": 8}), ("mana", "Mana", "text", {"width": 8}),
        ("hp_regen_per_second", "HP Regen (Sec)", "text", {"width": 6}),
        ("hp_regen_rate", "HP Regen Rate", "text", {"width": 6}),
        ("mana_regen_rate", "Mana Regen (Tic)", "text", {"width": 6}),
        ("STR", "Strength", "text", {"width": 6}), ("STA", "Stamina", "text", {"width": 6}), ("DEX", "Dexterity", "text", {"width": 6}),
        ("AGI", "Agility", "text", {"width": 6}), ("_INT", "Intelligence", "text", {"width": 6}), ("WIS", "Wisdom", "text", {"width": 6}),
        ("CHA", "Charisma", "text", {"width": 6}),
        ("spellscale", "Spell Scale", "text", {"width": 6}), ("healscale", "Heal Scale", "text", {"width": 6}),
        ("scalerate", "Scale Rate", "text", {"width": 6}), ("maxlevel", "Max Level", "text", {"width": 6}),
        ("heroic_strikethrough", "Heroic Strikethrough", "text", {"width": 6}),
    ]),
    ("Resists", 7, [
        ("MR", "Magic Resist", "text", {"width": 6}), ("CR", "Cold Resist", "text", {"width": 6}),
        ("DR", "Disease Resist", "text", {"width": 6}), ("FR", "Fire Resist", "text", {"width": 6}),
        ("PR", "Poison Resist", "text", {"width": 6}), ("Corrup", "Corruption Resist", "text", {"width": 6}),
        ("PhR", "Physical Resist", "text", {"width": 6}),
    ]),
    ("Combat & Awareness", 6, [
        ("mindmg", "Minimum Damage", "text"), ("maxdmg", "Maximum Damage", "text"),
        ("attack_count", "Attack Count", "dropdown", {"values": COMBAT_DROPDOWN_PRESETS["attack_count"]}),
        ("attack_speed", "Attack Speed", "dropdown", {"values": COMBAT_DROPDOWN_PRESETS["attack_speed"]}),
        ("attack_delay", "Attack Delay", "dropdown", {"values": COMBAT_DROPDOWN_PRESETS["attack_delay"]}),
        ("ATK", "Attack", "text"),
        ("Accuracy", "Accuracy", "dropdown", {"values": COMBAT_DROPDOWN_PRESETS["Accuracy"]}),
        ("Avoidance", "Avoidance", "dropdown", {"values": COMBAT_DROPDOWN_PRESETS["Avoidance"]}),
        ("slow_mitigation", "Slow Mitigation", "dropdown", {"values": COMBAT_DROPDOWN_PRESETS["slow_mitigation"]}),
        ("aggroradius", "Aggro Radius", "dropdown", {"values": COMBAT_DROPDOWN_PRESETS["aggroradius"]}),
        ("assistradius", "Assist Radius", "dropdown", {"values": COMBAT_DROPDOWN_PRESETS["assistradius"]}),
        ("npcspecialattks", "Spec Attacks", "text", {"width": 24}),
        ("always_aggro", "Always Aggro", "check", {"inline": True, "inline_reset": True}),
        ("npc_aggro", "NPC Aggro", "check", {"inline": True}),
        ("see_invis", "See Invis", "check", {"inline": True}), ("see_invis_undead", "See Invis Undead", "check", {"inline": True}),
        ("see_hide", "See Hide", "check", {"inline": True}), ("see_improved_hide", "See Improved Hide", "check", {"inline": True}),
    ]),
    ("Special Abilities", 3, SPECIAL_ABILITIES_FIELD_TUPLES),
    ("Weapon", 3, [
        ("d_melee_texture1", "Pri Weapon Model", "text"),
        ("prim_melee_type", "Pri Melee Type", "text"),
        ("sec_melee_type", "Sec Melee Type", "text"),
        ("d_melee_texture2", "Sec Weapon Model", "text"),
        ("ranged_type", "Ranged Type", "text"),
        ("ammo_idfile", "Ammo Model", "text"),
    ]),
]

# Flat list for the single Additional Attributes tree (order as defined here)
TREE_FIELD_SECTIONS = [
    ("alt_currency_id", "Alternate Currency ID", "text"),
    ("spawn_limit", "Spawn Limit", "text"),
    ("version", "Version", "text"),
    ("private_corpse", "Private Corpse", "check"),
    ("rare_spawn", "Rare Spawn", "check"),
    ("unique_spawn_by_name", "Unique Spawn By Name", "check"),
    ("unique_", "Unique Flag", "check"),
    ("exclude", "Exclude", "check"),
    ("fixed", "Fixed Spawn", "check"),
    ("ignore_despawn", "Ignore Despawn", "check"),
    ("herosforgemodel", "Heros Forge Model", "text"),
    ("armortint_id", "Armor Tint ID", "text"),
    ("armortint_red", "Armor Tint Red", "text"),
    ("armortint_green", "Armor Tint Green", "text"),
    ("armortint_blue", "Armor Tint Blue", "text"),
    ("npc_tint_id", "NPC Tint ID", "text"),
    ("armtexture", "Arm Texture", "text"),
    ("bracertexture", "Bracer Texture", "text"),
    ("handtexture", "Hand Texture", "text"),
    ("legtexture", "Leg Texture", "text"),
    ("feettexture", "Feet Texture", "text"),
    ("face", "Face", "text"),
    ("luclin_hairstyle", "Hairstyle", "text"),
    ("luclin_haircolor", "Haircolor", "text"),
    ("luclin_eyecolor", "Eyecolor 1", "text"),
    ("luclin_eyecolor2", "Eyecolor 2", "text"),
    ("luclin_beardcolor", "Beardcolor", "text"),
    ("luclin_beard", "Beard", "text"),
    ("drakkin_heritage", "(Drakkin) Heritage", "text"),
    ("drakkin_tattoo", "(Drakkin) Tattoo", "text"),
    ("drakkin_details", "(Drakkin) Details", "text"),
    ("qglobal", "QGlobal", "check"),
    ("isquest", "Is Quest NPC", "check"),
    ("isbot", "Is Bot", "check"),
    ("charm_ac", "Charm AC", "text"),
    ("charm_atk", "Charm ATK", "text"),
    ("charm_max_dmg", "Charm Max Damage", "text"),
    ("charm_min_dmg", "Charm Min Damage", "text"),
    ("charm_attack_delay", "Charm Attack Delay", "text"),
    ("charm_accuracy_rating", "Charm Accuracy Rating", "text"),
    ("charm_avoidance_rating", "Charm Avoidance Rating", "text"),
    ("adventure_template_id", "Adventure Template Id", "text"),
    ("trap_template", "Trap Template", "text"),
    ("peqid", "PEQ ID", "text"),
    ("npc_spells_effects_id", "Spell Effects ID", "text"),
]

class LookupDialog(tk.Toplevel):
    """Popup search dialog for selecting foreign key values."""

    def __init__(self, master, title, columns, fetcher, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.title(title)
        self.transient(master)
        self.grab_set()
        self.selected_id = None
        self.fetcher = fetcher
        self.columns = columns

        self.search_var = tk.StringVar()

        top = ttk.Frame(self, padding=6)
        top.pack(fill="both", expand=True)
        top.grid_columnconfigure(0, weight=1)

        search_row = ttk.Frame(top)
        search_row.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        search_row.grid_columnconfigure(1, weight=1)
        ttk.Label(search_row, text="Search:").grid(row=0, column=0, sticky="w", padx=(0, 4))
        entry = ttk.Entry(search_row, textvariable=self.search_var, width=30)
        entry.grid(row=0, column=1, sticky="ew")
        entry.bind("<Return>", lambda e: self._run_search())
        ttk.Button(search_row, text="Search", command=self._run_search).grid(row=0, column=2, padx=(4, 0))

        self.tree = ttk.Treeview(
            top,
            columns=[c[0] for c in columns],
            show="headings",
            selectmode="browse",
            height=12,
        )
        for col_id, col_label in columns:
            self.tree.heading(col_id, text=col_label)
            self.tree.column(col_id, width=120, anchor="w")

        vsb = ttk.Scrollbar(top, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        top.grid_rowconfigure(1, weight=1)

        btns = ttk.Frame(top)
        btns.grid(row=2, column=0, columnspan=2, sticky="e", pady=(6, 0))
        ttk.Button(btns, text="Select", command=self._select_current).pack(side="right", padx=(4, 0))
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="right")

        self.tree.bind("<Double-1>", lambda e: self._select_current())
        self._run_search()
        entry.focus_set()

    def _run_search(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            rows = self.fetcher(self.search_var.get().strip())
        except Exception as exc:
            messagebox.showerror("Lookup Error", str(exc), parent=self)
            return
        col_ids = [c[0] for c in self.columns]
        for row in rows:
            val_dict = row if isinstance(row, dict) else {}
            values = [val_dict.get(cid, "") if isinstance(val_dict, dict) else "" for cid in col_ids]
            item = self.tree.insert("", "end", values=values)
            self.tree.set(item, col_ids[0], val_dict.get(col_ids[0], ""))

    def _select_current(self):
        sel = self.tree.selection()
        if not sel:
            return
        first_col = self.columns[0][0]
        try:
            self.selected_id = self.tree.set(sel[0], first_col)
        except Exception:
            self.selected_id = None
        self.destroy()


class NPCSearchDialog(tk.Toplevel):
    """Popup search dialog for finding NPCs by ID, name, or zone-derived ID range."""

    def __init__(self, master, fetcher, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.title("Search NPCs")
        self.transient(master)
        self.grab_set()
        self.selected_id = None
        self.fetcher = fetcher

        self.name_var = tk.StringVar()
        self.id_min_var = tk.StringVar()
        self.id_max_var = tk.StringVar()
        self.zone_var = tk.StringVar()

        top = ttk.Frame(self, padding=8)
        top.pack(fill="both", expand=True)
        top.grid_columnconfigure(3, weight=1)

        ttk.Label(top, text="Name contains:").grid(row=0, column=0, sticky="w", padx=(0, 4))
        name_entry = ttk.Entry(top, textvariable=self.name_var, width=22)
        name_entry.grid(row=0, column=1, sticky="w")

        ttk.Label(top, text="ID min-max:").grid(row=0, column=2, sticky="e", padx=(8, 4))
        id_min_entry = ttk.Entry(top, textvariable=self.id_min_var, width=10)
        id_min_entry.grid(row=0, column=3, sticky="w")
        ttk.Label(top, text="to").grid(row=0, column=4, sticky="w", padx=(4, 4))
        id_max_entry = ttk.Entry(top, textvariable=self.id_max_var, width=10)
        id_max_entry.grid(row=0, column=5, sticky="w")

        ttk.Label(top, text="Zone ID:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        zone_entry = ttk.Entry(top, textvariable=self.zone_var, width=10)
        zone_entry.grid(row=1, column=1, sticky="w", pady=(6, 0))
        ttk.Label(top, text="(zoneid x 1000 range)").grid(row=1, column=2, columnspan=2, sticky="w", pady=(6, 0))

        ttk.Button(top, text="Search", command=self._run_search).grid(row=1, column=5, sticky="e", pady=(6, 0))

        self.tree = ttk.Treeview(
            top,
            columns=["id", "name", "level", "race", "class"],
            show="headings",
            selectmode="browse",
            height=14,
        )
        for col_id, col_label, width in [
            ("id", "ID", 70),
            ("name", "Name", 220),
            ("level", "Lvl", 60),
            ("race", "Race", 80),
            ("class", "Class", 80),
        ]:
            self.tree.heading(col_id, text=col_label)
            self.tree.column(col_id, width=width, anchor="w")

        vsb = ttk.Scrollbar(top, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=2, column=0, columnspan=6, sticky="nsew", pady=(8, 0))
        vsb.grid(row=2, column=6, sticky="ns", pady=(8, 0))
        top.grid_rowconfigure(2, weight=1)
        top.grid_columnconfigure(5, weight=1)

        btns = ttk.Frame(top)
        btns.grid(row=3, column=0, columnspan=7, sticky="e", pady=(8, 0))
        ttk.Button(btns, text="Select", command=self._select_current).pack(side="right", padx=(4, 0))
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="right")

        self.tree.bind("<Double-1>", lambda e: self._select_current())
        for widget in (name_entry, id_min_entry, id_max_entry, zone_entry):
            widget.bind("<Return>", lambda _e: self._run_search())
        name_entry.focus_set()
        self._run_search()

    def _run_search(self):
        filters = {
            "name": self.name_var.get().strip(),
            "id_min": self.id_min_var.get().strip(),
            "id_max": self.id_max_var.get().strip(),
            "zone": self.zone_var.get().strip(),
        }
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            rows = self.fetcher(filters)
        except Exception as exc:
            messagebox.showerror("Search Error", str(exc), parent=self)
            return
        for row in rows:
            if isinstance(row, dict):
                values = [row.get("id", ""), row.get("name", ""), row.get("level", ""), row.get("race", ""), row.get("class", "")]
            else:
                values = list(row)
            item = self.tree.insert("", "end", values=values)
            try:
                self.tree.set(item, "id", values[0])
            except Exception:
                pass

    def _select_current(self):
        sel = self.tree.selection()
        if not sel:
            return
        try:
            self.selected_id = self.tree.set(sel[0], "id")
        except Exception:
            self.selected_id = None
        self.destroy()

class NPCEditorTool:
    """NPC editor embedded inside the EQ Tools tab layout."""

    def __init__(self, parent_frame, db_manager):
        self.parent = parent_frame
        self.db_manager = db_manager
        self.fields = {}
        self.current_data = None
        self.status_var = tk.StringVar(value="Enter an NPC ID to begin.")
        self.npcid_var = tk.StringVar()
        self.preview_canvas = None
        self.preview_bg_image = None
        self.preview_npc_image = None
        self.preview_renders = []
        self.related_text = None
        self.default_field_columns = 3
        self.entry_width = 6
        self.field_definitions = {}
        self.additional_tree = None
        self.additional_tree_item = None
        self.additional_columns = []
        self.special_ability_specs = SPECIAL_ABILITY_SPECS
        self.fields["special_abilities"] = tk.StringVar()
        self.field_definitions["special_abilities"] = {"label": "Special Abilities", "type": "text", "options": {}}
        # Style identifiers for slimmer, flatter scrollbars so they blend into the dark UI
        self.scrollbar_style = "Minimal.Vertical.TScrollbar"
        self.scrollbar_h_style = "Minimal.Horizontal.TScrollbar"
        self.tree_style = "Compact.Treeview"
        self.weapon_section = None

        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self._build_top_bar()
        self._build_main_content()
        self._sync_special_fields_from_string(self.fields["special_abilities"].get())
        self._refresh_preview()
        self._refresh_related_references()
        self._configure_scrollbar_styles()

    def _build_top_bar(self):
        topf = ttk.Frame(self.main_frame, padding=(6, 6, 6, 2))
        topf.grid(row=0, column=0, sticky="ew")
        for col in range(9):
            topf.grid_columnconfigure(col, weight=0)
        topf.grid_columnconfigure(9, weight=1)

        ttk.Label(topf, text="NPC ID:").grid(row=0, column=0, sticky="w")
        tk.Entry(topf, textvariable=self.npcid_var, width=12).grid(row=0, column=1, padx=(4, 4))
        ttk.Button(topf, text="Load", command=self._load_npc).grid(row=0, column=2, padx=(0, 4))
        ttk.Button(topf, text="Search...", command=self._open_npc_search_dialog).grid(row=0, column=3, padx=(0, 4))
        ttk.Button(topf, text="New", command=self.clear_fields).grid(row=0, column=4, padx=(0, 4))
        ttk.Button(topf, text="Create", command=self._create_npc).grid(row=0, column=5, padx=(0, 4))
        self.save_button = ttk.Button(topf, text="Save", command=self._save_npc, state="disabled")
        self.save_button.grid(row=0, column=6, padx=(0, 4))
        ttk.Button(topf, text="Refresh Preview", command=self._refresh_preview).grid(row=0, column=7, sticky="w")

        status_label = ttk.Label(topf, textvariable=self.status_var, foreground="#a6a6a6")
        status_label.grid(row=0, column=8, sticky="w", padx=(10, 0))

    def _build_main_content(self):
        self.content_frame = ttk.Frame(self.main_frame, padding=(6, 0, 0, 6))
        self.content_frame.grid(row=1, column=0, sticky="nsew")
        self.content_frame.grid_rowconfigure(0, weight=2)
        self.content_frame.grid_rowconfigure(1, weight=0)
        # Keep the details panel wide enough for fields while leaving room for the right panels
        self.content_frame.grid_columnconfigure(0, weight=1, minsize=1100)
        self.content_frame.grid_columnconfigure(1, weight=0, minsize=180)

        self._build_details_panel()
        self._build_side_panel()
        self._build_additional_tree()

    def _build_details_panel(self):
        details_container = ttk.Frame(self.content_frame, relief=tk.SUNKEN, borderwidth=1)
        details_container.grid(row=0, column=0, sticky="nsew")
        details_container.grid_rowconfigure(0, weight=1)
        details_container.grid_columnconfigure(0, weight=1)

        self.details_canvas = tk.Canvas(details_container, highlightthickness=0)
        self.details_canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(details_container, orient="vertical", command=self.details_canvas.yview)
        scrollbar.configure(style=self.scrollbar_style)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.details_canvas.configure(yscrollcommand=scrollbar.set)

        self.details_inner = ttk.Frame(self.details_canvas)
        self.details_inner_window = self.details_canvas.create_window((0, 0), window=self.details_inner, anchor="nw")
        self.details_canvas.bind(
            "<Configure>",
            lambda event: self.details_canvas.itemconfigure(self.details_inner_window, width=event.width),
        )
        self.details_inner.bind(
            "<Configure>",
            lambda event: self.details_canvas.configure(scrollregion=self.details_canvas.bbox("all"))
        )
        self.details_inner.grid_columnconfigure(0, weight=1)

        for idx, (section_name, column_count, fields) in enumerate(ENTRY_FIELD_SECTIONS):
            if section_name == "Weapon":
                # Defer Weapons to the right-hand stack under the preview
                self.weapon_section = (section_name, column_count, fields)
                continue
            section = ttk.LabelFrame(self.details_inner, text=section_name)
            section.grid(row=idx, column=0, sticky="ew", padx=6, pady=4)
            if section_name == "Special Abilities":
                self._build_special_abilities_section(section)
            else:
                self._populate_fields(section, fields, column_count)

    def _build_side_panel(self):
        side_panel = ttk.Frame(self.content_frame)
        side_panel.grid(row=0, column=1, sticky="ne", padx=0)
        side_panel.grid_rowconfigure(2, weight=1)

        self._build_preview_panel(side_panel)
        self._build_weapon_panel(side_panel)
        self._build_related_panel(side_panel, row=2)

    def _build_preview_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="NPC Preview")
        frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(0, 5))
        frame.grid_columnconfigure(0, weight=1)

        self.preview_canvas = tk.Canvas(frame, width=230, height=180, highlightthickness=0)
        self.preview_canvas.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=4, pady=4)
        self._initialize_preview_background()

        ttk.Button(frame, text="Update Preview", command=self._refresh_preview).grid(row=1, column=0, sticky="w", padx=4, pady=(0, 4))

    def _initialize_preview_background(self):
        max_width, max_height = 230, 180
        try:
            img = Image.open(os.path.join(os.path.dirname(__file__), "..", "images", "other", "default.jpg"))
            img.thumbnail((max_width, max_height), Image.LANCZOS)
            self.preview_bg_image = ImageTk.PhotoImage(img)
            self.preview_canvas.config(width=max_width, height=max_height)
        except Exception:
            self.preview_bg_image = None
            self.preview_canvas.config(width=max_width, height=max_height)

    def _build_weapon_panel(self, parent):
        if not self.weapon_section:
            return
        section_name, column_count, fields = self.weapon_section
        frame = ttk.LabelFrame(parent, text=section_name)
        frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        frame.grid_columnconfigure(0, weight=1)
        self._populate_fields(frame, fields, column_count)

    def _build_related_panel(self, parent, row=1):
        frame = ttk.LabelFrame(parent, text="Linked Tables")
        frame.grid(row=row, column=0, sticky="nsew", padx=5, pady=5)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        ttk.Button(frame, text="Reload Linked Data", command=self._refresh_related_references).grid(row=0, column=0, sticky="w", padx=4, pady=4)
        # Keep this narrow so the side panel doesn't demand excessive width
        self.related_text = tk.Text(frame, height=14, width=36, wrap="word")
        self.related_text.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 4))
        self.related_text.configure(
            state="disabled",
            background="#2d2d2d",
            foreground="#f5f5f5",
            insertbackground="#f5f5f5",
            relief="sunken",
            borderwidth=1,
        )
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.related_text.yview)
        scrollbar.configure(style=self.scrollbar_style)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.related_text.configure(yscrollcommand=scrollbar.set)

    def _normalize_field_definition(self, field):
        if len(field) == 3:
            fkey, flabel, ftype = field
            fopts = {}
        else:
            fkey, flabel, ftype, extra = field
            fopts = extra if isinstance(extra, dict) else {"values": extra}
        return fkey, flabel, ftype, fopts

    def _register_field(self, key, label, ftype, options):
        if key not in self.field_definitions:
            self.field_definitions[key] = {"label": label, "type": ftype, "options": options or {}}

    def _ensure_field_variable(self, fkey, ftype):
        if fkey in self.fields:
            return self.fields[fkey]
        if ftype == "check":
            var = tk.IntVar()
        else:
            var = tk.StringVar()
        self.fields[fkey] = var
        return var

    def _create_checkbutton(self, parent, text, variable):
        return tk.Checkbutton(
            parent,
            text=text,
            variable=variable,
            fg="#ffffff",
            bg="#2d2d2d",
            activeforeground="#ffffff",
            activebackground="#3c3c3c",
            selectcolor="#2d2d2d",
            font=("Arial", 8),
            highlightthickness=0,
            bd=0,
        )

    def _parse_special_abilities_string(self, value):
        parsed = {}
        for chunk in (value or "").split("^"):
            parts = chunk.split(",")
            if not parts or not parts[0].isdigit():
                continue
            idx = int(parts[0])
            parsed[idx] = parts[1:]
        return parsed

    def _rebuild_special_abilities_string(self):
        parts = []
        for spec in self.special_ability_specs:
            enable_var = self.fields.get(spec["enable_key"])
            if not isinstance(enable_var, tk.IntVar) or not enable_var.get():
                continue
            values = []
            for p_key, p_default in spec.get("param_keys", []):
                var = self.fields.get(p_key)
                val = var.get().strip() if isinstance(var, tk.StringVar) else ""
                values.append(val if val else (p_default if p_default != "" else "1"))
            if not values:
                values.append("1")
            parts.append(",".join([str(spec["id"])] + values))
        self.fields["special_abilities"].set("^".join(parts))

    def _sync_special_fields_from_string(self, value):
        parsed = self._parse_special_abilities_string(value)
        for spec in self.special_ability_specs:
            enable_var = self.fields.get(spec["enable_key"])
            if isinstance(enable_var, tk.IntVar):
                enable_var.set(1 if spec["id"] in parsed else 0)
            params = parsed.get(spec["id"], [])
            for idx, (p_key, p_default) in enumerate(spec.get("param_keys", [])):
                var = self.fields.get(p_key)
                if isinstance(var, tk.StringVar):
                    var.set(params[idx] if idx < len(params) else p_default)
    def _lookup_query_for(self, lookup_type, search):
        term = (search or "").strip()
        like = f"%{term}%"
        if lookup_type == "npc_spells":
            where = ""
            params = ()
            if term:
                if term.isdigit():
                    where = "WHERE id = %s OR name LIKE %s"
                    params = (int(term), like)
                else:
                    where = "WHERE name LIKE %s"
                    params = (like,)
            query = f"""
                SELECT id, COALESCE(name, '') AS name
                FROM npc_spells
                {where}
                ORDER BY id
                LIMIT 200
            """
            return query, params
        if lookup_type == "npc_spells_effects":
            where = ""
            params = ()
            if term:
                if term.isdigit():
                    where = "WHERE id = %s OR name LIKE %s"
                    params = (int(term), like)
                else:
                    where = "WHERE name LIKE %s"
                    params = (like,)
            query = f"""
                SELECT id, COALESCE(name, '') AS name
                FROM npc_spells_effects
                {where}
                ORDER BY id
                LIMIT 200
            """
            return query, params
        if lookup_type == "merchant":
            where = ""
            params = ()
            if term and term.isdigit():
                where = "WHERE ml.merchantid = %s"
                params = (int(term),)
            query = f"""
                SELECT ml.merchantid AS id,
                       COUNT(*) AS items,
                       (
                           SELECT GROUP_CONCAT(CONCAT(ml2.item, ':', COALESCE(i2.Name, '')) ORDER BY ml2.item SEPARATOR '; ')
                           FROM merchantlist ml2
                           LEFT JOIN items i2 ON ml2.item = i2.id
                           WHERE ml2.merchantid = ml.merchantid
                           ORDER BY ml2.item
                           LIMIT 3
                       ) AS sample_items
                FROM merchantlist ml
                {where}
                GROUP BY ml.merchantid
                ORDER BY ml.merchantid
                LIMIT 200
            """
            return query, params
        return "", ()

    def _open_lookup_dialog(self, fkey, target_var):
        cfg = LOOKUP_CONFIG.get(fkey)
        if not cfg:
            return

        def _fetch(search):
            query, params = self._lookup_query_for(cfg.get("type"), search)
            if not query:
                return []
            return self._fetch_rows(query, params)

        dlg = LookupDialog(self.main_frame, cfg.get("title", "Lookup"), cfg.get("columns", []), _fetch)
        if dlg.selected_id is not None:
            try:
                target_var.set(str(dlg.selected_id))
            except Exception:
                pass
            self._update_additional_tree_values()

    def _open_npc_search_dialog(self):
        def _fetch(filters):
            return self._search_npcs(filters)

        dlg = NPCSearchDialog(self.main_frame, _fetch)
        dlg.wait_window()
        if dlg.selected_id:
            try:
                self.npcid_var.set(str(dlg.selected_id))
            except Exception:
                pass
            self._load_npc()

    def _search_npcs(self, filters):
        name = (filters.get("name") or "").strip()
        id_min = filters.get("id_min") or ""
        id_max = filters.get("id_max") or ""
        zone = filters.get("zone") or ""
        conditions = []
        params = []
        if name:
            conditions.append("LOWER(name) LIKE %s")
            params.append(f"%{name.lower()}%")
        if id_min:
            try:
                val = int(id_min)
                conditions.append("id >= %s")
                params.append(val)
            except ValueError:
                pass
        if id_max:
            try:
                val = int(id_max)
                conditions.append("id <= %s")
                params.append(val)
            except ValueError:
                pass
        if zone:
            try:
                zid = int(zone)
                low = zid * 1000
                high = low + 999
                conditions.append("id BETWEEN %s AND %s")
                params.extend([low, high])
            except ValueError:
                pass
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        query = f"""
            SELECT id, COALESCE(name, '') AS name, level, race, class
            FROM npc_types
            {where_clause}
            ORDER BY id
            LIMIT 200
        """
        return self._fetch_rows(query, tuple(params))

    def _populate_fields(self, frame, fields, columns=None, start_row=0):
        columns = columns or self.default_field_columns
        total_columns = columns * 2
        for col in range(total_columns):
            frame.grid_columnconfigure(col, weight=1 if col % 2 == 1 else 0)

        row = start_row
        col_slot = 0

        for field in fields:
            fkey, flabel, ftype, fopts = self._normalize_field_definition(field)
            self._register_field(fkey, flabel, ftype, fopts)
            if ftype == "check":
                fullrow = fopts.get("fullrow", False)
                inline = fopts.get("inline", not fullrow)
                v = self._ensure_field_variable(fkey, ftype)
                if inline:
                    if fopts.get("inline_reset") and col_slot != 0:
                        row += 1
                        col_slot = 0
                    label_col = col_slot * 2
                    cb = self._create_checkbutton(frame, flabel, v)
                    cb.grid(row=row, column=label_col, columnspan=2, sticky="w", padx=5, pady=2)
                    col_slot += 1
                    if col_slot >= columns:
                        row += 1
                        col_slot = 0
                else:
                    if col_slot != 0:
                        row += 1
                        col_slot = 0
                    cb = self._create_checkbutton(frame, flabel, v)
                    cb.grid(row=row, column=0, columnspan=total_columns, sticky="w", padx=5, pady=2)
                    row += 1
                self.fields[fkey] = v
                continue
            if ftype == "textarea":
                if col_slot != 0:
                    row += 1
                    col_slot = 0
                lbl = ttk.Label(frame, text=flabel)
                lbl.grid(row=row, column=0, sticky="ne", padx=5, pady=2)
                t = tk.Text(frame, height=3, width=50)
                t.grid(row=row, column=1, columnspan=total_columns - 1, sticky="ew", padx=5, pady=2)
                self.fields[fkey] = t
                row += 1
                continue
            if ftype == "dropdown":
                label_col = col_slot * 2
                entry_col = label_col + 1
                lbl = ttk.Label(frame, text=flabel)
                lbl.grid(row=row, column=label_col, sticky="e", padx=5, pady=2)
                v = self._ensure_field_variable(fkey, ftype)
                width = fopts.get("width", self.entry_width)
                state = "normal" if fopts.get("allow_custom", True) else "readonly"
                cb = ttk.Combobox(frame, textvariable=v, width=width, state=state, values=fopts.get("values", []))
                if "default" in fopts:
                    v.set(fopts["default"])
                cb.grid(row=row, column=entry_col, sticky="ew", padx=5, pady=2)
                self.fields[fkey] = v

                col_slot += 1
                if col_slot >= columns:
                    row += 1
                    col_slot = 0
                continue

            label_col = col_slot * 2
            entry_col = label_col + 1
            lbl = ttk.Label(frame, text=flabel)
            lbl.grid(row=row, column=label_col, sticky="e", padx=5, pady=2)
            v = self._ensure_field_variable(fkey, ftype)
            holder = ttk.Frame(frame)
            holder.grid(row=row, column=entry_col, sticky="ew", padx=5, pady=2)
            holder.grid_columnconfigure(0, weight=1)
            width = fopts.get("width", self.entry_width)
            ent = ttk.Entry(holder, textvariable=v, width=width)
            ent.grid(row=0, column=0, sticky="ew")
            if fkey in LOOKUP_CONFIG:
                ttk.Button(
                    holder,
                    text="Find...",
                    command=lambda key=fkey, var=v: self._open_lookup_dialog(key, var),
                    width=7,
                ).grid(row=0, column=1, padx=(4, 0))
            self.fields[fkey] = v

            col_slot += 1
            if col_slot >= columns:
                row += 1
                col_slot = 0

    def _build_special_abilities_section(self, frame):
        """Two-column layout: heavy param abilities on the left, compact ones on the right."""
        frame.grid_columnconfigure(0, weight=2)
        frame.grid_columnconfigure(1, weight=1)

        left_prefixes = {
            "sa_summon",
            "sa_enrage",
            "sa_rampage",
            "sa_ae_rampage",
            "sa_flurry",
            "sa_ranged_attack",
        }

        # Register all fields up front so variables/definitions exist
        field_meta = {}
        for fkey, flabel, ftype, fopts in SPECIAL_ABILITIES_FIELD_TUPLES:
            self._register_field(fkey, flabel, ftype, fopts)
            self._ensure_field_variable(fkey, ftype)
            field_meta[fkey] = (flabel, ftype, fopts)

        left_specs = [spec for spec in SPECIAL_ABILITY_SPECS if any(spec["enable_key"].startswith(p) for p in left_prefixes)]
        right_fields = [f for f in SPECIAL_ABILITIES_FIELD_TUPLES if not any(f[0].startswith(p) for p in left_prefixes)]
        heavy_right_specs = [
            spec for spec in SPECIAL_ABILITY_SPECS
            if spec["enable_key"] in {"sa_counter_avoid_damage", "sa_modify_avoid_damage"}
        ]
        heavy_right_keys = {spec["enable_key"] for spec in heavy_right_specs}
        heavy_right_param_keys = {p_key for spec in heavy_right_specs for p_key, _ in spec.get("param_keys", [])}
        right_fields = [f for f in right_fields if f[0] not in heavy_right_keys and f[0] not in heavy_right_param_keys]

        left = ttk.Frame(frame)
        right = ttk.Frame(frame)
        left.grid(row=0, column=0, sticky="nsew", padx=(4, 2), pady=2)
        right.grid(row=0, column=1, sticky="nsew", padx=(2, 4), pady=2)
        right.grid_columnconfigure(0, weight=1)
        right.grid_columnconfigure(1, weight=1)

        # Build bordered groups for the multi-param abilities on the left, two per row
        for idx, spec in enumerate(left_specs):
            enable_key = spec["enable_key"]
            label = field_meta.get(enable_key, (enable_key, "", {}))[0]
            group = ttk.LabelFrame(left, text=label, borderwidth=1, relief="groove")
            group_row = idx // 2
            group_col = idx % 2
            left.grid_columnconfigure(group_col, weight=1)
            group.grid(row=group_row, column=group_col, sticky="nsew", padx=2, pady=3)
            group.grid_columnconfigure(0, weight=1)

            # Enable checkbox
            v = self._ensure_field_variable(enable_key, "check")
            cb = self._create_checkbutton(group, label, v)
            cb.grid(row=0, column=0, sticky="w", padx=4, pady=2)

            # Params beneath, wrapped into two columns
            param_fields = []
            for p_key, _ in spec.get("param_keys", []):
                flabel, ftype, fopts = field_meta.get(p_key, (p_key, "text", {}))
                param_fields.append((p_key, flabel, ftype, fopts))
            if param_fields:
                self._populate_fields(group, param_fields, columns=1, start_row=1)

        # More columns on right to condense checkbox/single-param entries.
        # Force checkboxes inline so they don't stack as full rows.
        adjusted_right_fields = []
        for fkey, flabel, ftype, fopts in right_fields:
            opts = dict(fopts)
            if ftype == "check":
                opts.pop("fullrow", None)
                opts["inline"] = True
            adjusted_right_fields.append((fkey, flabel, ftype, opts))
        right_group = ttk.LabelFrame(right, text="Other Abilities", borderwidth=1, relief="groove")
        right_group.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=2, pady=2)
        right_group.grid_columnconfigure(0, weight=1)
        self._populate_fields(right_group, adjusted_right_fields, columns=4)

        # Bordered heavy-parameter abilities on right, stacked below Other Abilities
        for idx, spec in enumerate(heavy_right_specs):
            enable_key = spec["enable_key"]
            label = field_meta.get(enable_key, (enable_key, "", {}))[0]
            group = ttk.LabelFrame(right, text=label, borderwidth=1, relief="groove")
            group_row = 1 + (idx // 2)
            group_col = idx % 2
            right.grid_columnconfigure(group_col, weight=1)
            group.grid(row=group_row, column=group_col, sticky="nsew", padx=2, pady=3)
            group.grid_columnconfigure(0, weight=1)

            v = self._ensure_field_variable(enable_key, "check")
            cb = self._create_checkbutton(group, label, v)
            cb.grid(row=0, column=0, sticky="w", padx=4, pady=2)

            param_fields = []
            for p_key, _ in spec.get("param_keys", []):
                flabel, ftype, fopts = field_meta.get(p_key, (p_key, "text", {}))
                param_fields.append((p_key, flabel, ftype, fopts))
            if param_fields:
                self._populate_fields(group, param_fields, columns=1, start_row=1)

    def _build_additional_tree(self):
        container = ttk.LabelFrame(self.content_frame, text="Additional Attributes")
        container.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=6, pady=(4, 6))
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        # Prevent the wide treeview columns from forcing the whole layout wider than the viewport
        container.configure(width=1100, height=90)
        container.grid_propagate(False)

        self.additional_columns = []
        for field in TREE_FIELD_SECTIONS:
            fkey, flabel, ftype, fopts = self._normalize_field_definition(field)
            self._register_field(fkey, flabel, ftype, fopts)
            self._ensure_field_variable(fkey, ftype)
            self.additional_columns.append((fkey, flabel, ftype))

        column_ids = [fkey for fkey, _, _ in self.additional_columns]
        self.additional_tree_hsb = None
        self.additional_tree = ttk.Treeview(
            container,
            columns=column_ids,
            show="headings",
            selectmode="browse",
            height=4,
            style=self.tree_style,
        )
        hsb = ttk.Scrollbar(container, orient="horizontal", command=self.additional_tree.xview, style=self.scrollbar_h_style)
        vsb = ttk.Scrollbar(container, orient="vertical", command=self.additional_tree.yview, style=self.scrollbar_style)
        self.additional_tree_hsb = hsb
        self.additional_tree.configure(xscrollcommand=hsb.set, yscrollcommand=vsb.set)

        for fkey, flabel, _ in self.additional_columns:
            self.additional_tree.heading(fkey, text=flabel)
            self.additional_tree.column(fkey, width=90, anchor="w", stretch=False)

        self.additional_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        # Hide the horizontal scrollbar unless needed to avoid a stray line when content fits
        hsb.grid_remove()

        self.additional_tree_item = self.additional_tree.insert(
            "",
            "end",
            values=[self._format_tree_value(fkey) for fkey in column_ids],
        )
        self.additional_tree.bind("<Double-1>", self._on_additional_tree_edit)
        self.additional_tree.bind("<Configure>", lambda _e: self._update_additional_tree_scrollbars())
        self._enable_tree_mousewheel(self.additional_tree)
        self._update_additional_tree_scrollbars()

    def _format_tree_value(self, key):
        val = self._get_field_value(key)
        var = self.fields.get(key)
        if isinstance(var, tk.IntVar):
            return "Yes" if var.get() else "No"
        if val is None or str(val).strip() == "":
            return "-"
        return str(val)

    def _update_additional_tree_values(self):
        if not self.additional_tree or not self.additional_tree_item:
            return
        values = [self._format_tree_value(fkey) for fkey, _, _ in self.additional_columns]
        self.additional_tree.item(self.additional_tree_item, values=values)

    def _on_additional_tree_edit(self, event):
        if not self.additional_tree:
            return
        row = self.additional_tree.identify_row(event.y)
        col_id = self.additional_tree.identify_column(event.x)
        if not row or row != self.additional_tree_item:
            return
        if not col_id.startswith("#"):
            return
        try:
            idx = int(col_id.lstrip("#")) - 1
        except ValueError:
            return
        if idx < 0 or idx >= len(self.additional_columns):
            return

        field_key, _, _ = self.additional_columns[idx]
        meta = self.field_definitions.get(field_key, {})
        var = self.fields.get(field_key)
        ftype = meta.get("type")
        if ftype == "check" and isinstance(var, tk.IntVar):
            var.set(0 if var.get() else 1)
            self._update_additional_tree_values()
            return

        bbox = self.additional_tree.bbox(row, col_id)
        if not bbox:
            return
        x, y, width, height = bbox

        edit_var = tk.StringVar(value=self._get_field_value(field_key))
        entry = ttk.Entry(self.additional_tree, textvariable=edit_var)
        entry.place(x=x, y=y, width=width, height=height)
        entry.focus_set()

        def _commit(event=None):
            new_val = edit_var.get()
            target = self.fields.get(field_key)
            if isinstance(target, tk.IntVar):
                try:
                    target.set(int(new_val))
                except ValueError:
                    messagebox.showerror("Invalid value", f"{meta.get('label', field_key)} must be numeric.")
                    entry.destroy()
                    return
            elif isinstance(target, tk.StringVar):
                target.set(new_val)
            self._update_additional_tree_values()
            entry.destroy()

        def _cancel(event=None):
            entry.destroy()

        entry.bind("<Return>", _commit)
        entry.bind("<Escape>", _cancel)
        entry.bind("<FocusOut>", _commit)

    def _enable_tree_mousewheel(self, tree):
        def _on_mousewheel(event):
            try:
                delta = int(-1 * (event.delta / 120))
                tree.yview_scroll(delta, "units")
            except Exception:
                pass
            return "break"

        def _on_linux_scroll_up(event):
            tree.yview_scroll(-1, "units")
            return "break"

        def _on_linux_scroll_down(event):
            tree.yview_scroll(1, "units")
            return "break"

        try:
            tree.bind("<MouseWheel>", _on_mousewheel, add=True)
            tree.bind("<Button-4>", _on_linux_scroll_up, add=True)
            tree.bind("<Button-5>", _on_linux_scroll_down, add=True)
        except Exception:
            pass

    def _update_additional_tree_scrollbars(self):
        """Show the horizontal scrollbar only when the columns overflow the available width."""
        if not self.additional_tree or not self.additional_tree_hsb:
            return
        try:
            self.additional_tree.update_idletasks()
            total_width = sum(self.additional_tree.column(col, "width") for col in self.additional_tree["columns"])
            visible_width = self.additional_tree.winfo_width()
            if total_width > visible_width + 4:
                self.additional_tree.configure(xscrollcommand=self.additional_tree_hsb.set)
                self.additional_tree_hsb.grid()
            else:
                self.additional_tree.configure(xscrollcommand=None)
                self.additional_tree_hsb.grid_remove()
        except Exception:
            # If anything goes wrong, fall back to showing the scrollbar
            try:
                self.additional_tree.configure(xscrollcommand=self.additional_tree_hsb.set)
                self.additional_tree_hsb.grid()
            except Exception:
                pass

    def _configure_scrollbar_styles(self):
        """Create subtle scrollbar styles that blend into the dark UI, plus compact tree styling."""
        try:
            style = ttk.Style(self.parent)
            style.configure(
                self.scrollbar_style,
                gripcount=0,
                background="#3c3c3c",
                darkcolor="#2a2a2a",
                lightcolor="#2a2a2a",
                troughcolor="#1f1f1f",
                bordercolor="#1f1f1f",
                arrowcolor="#cfcfcf",
                relief="flat",
            )
            style.configure(
                self.scrollbar_h_style,
                gripcount=0,
                background="#3c3c3c",
                darkcolor="#2a2a2a",
                lightcolor="#2a2a2a",
                troughcolor="#1f1f1f",
                bordercolor="#1f1f1f",
                arrowcolor="#cfcfcf",
                relief="flat",
            )
            style.map(self.scrollbar_style, background=[("active", "#4a4a4a")])
            style.map(self.scrollbar_h_style, background=[("active", "#4a4a4a")])
            # Compact tree headers/rows to reduce visual height
            style.configure(self.tree_style, rowheight=20)
            style.configure(f"{self.tree_style}.Heading", padding=(2, 1))
        except Exception:
            # If theme doesn't support these options, silently continue with defaults
            pass

    def _refresh_preview(self):
        if not self.preview_canvas:
            return
        self._update_additional_tree_values()
        self.preview_canvas.update_idletasks()
        max_w = self.preview_canvas.winfo_width() or int(self.preview_canvas.cget("width"))
        max_h = self.preview_canvas.winfo_height() or int(self.preview_canvas.cget("height"))
        self.preview_canvas.delete("all")
        self.preview_renders = []

        # Build ordered list: race image first, then primary/secondary (and ammo if present)
        image_entries = []
        race_path = self._get_preview_image_path()
        if race_path:
            image_entries.append({"path": race_path, "label": None})
        weapon_paths = self._get_weapon_image_paths()
        for path, label in weapon_paths:
            image_entries.append({"path": path, "label": label})

        self._draw_preview_background(max_w, max_h, use_default=not bool(image_entries))

        if not image_entries:
            self._draw_preview_placeholder("No preview available.")
            return

        try:
            self._layout_preview_images(image_entries, max_w, max_h)
        except Exception as exc:
            self._draw_preview_placeholder("No preview available.")

    def _get_preview_image_path(self):
        """Pick the best NPC preview image based on race/gender/texture/helm."""
        race = self._safe_int(self._get_field_value("race"))
        if race is None:
            return None
        gender = self._safe_int(self._get_field_value("gender"))
        texture = self._safe_int(self._get_field_value("texture"))
        helm = self._safe_int(self._get_field_value("helmtexture"))
        pattern = os.path.join(os.path.dirname(__file__), "..", "images", "raceimages", f"{race}_*.jpg")
        candidates = glob.glob(pattern)
        if not candidates:
            return None

        def score(path):
            base = os.path.basename(path).replace(".jpg", "")
            parts = base.split("_")
            s = 0
            try:
                p_gender = int(parts[1]) if len(parts) > 1 else None
                p_texture = int(parts[2]) if len(parts) > 2 else None
                p_helm = int(parts[3]) if len(parts) > 3 else None
            except Exception:
                p_gender = p_texture = p_helm = None
            if gender is not None and p_gender == gender:
                s += 8
            elif gender is None and p_gender == 2:
                s += 2
            if texture is not None and p_texture == texture:
                s += 4
            if helm is not None and p_helm == helm:
                s += 1
            return -s

        candidates.sort(key=score)
        return candidates[0]

    def _get_weapon_image_paths(self):
        """Return available weapon image paths for primary, secondary, and ammo models."""
        weapon_keys = [
            ("d_melee_texture1", "primary"),
            ("d_melee_texture2", "secondary"),
            ("ammo_idfile", "ammo"),
        ]
        paths = []
        for key, _label in weapon_keys:
            raw = self._get_field_value(key)
            if not raw:
                continue
            # Suppress default ammo placeholder IT10
            if key == "ammo_idfile" and str(raw).strip().lower() in ("it10", "10"):
                continue
            if isinstance(raw, str):
                cleaned = raw.strip().lower()
                if cleaned.startswith("it"):
                    cleaned = cleaned[2:]
            else:
                cleaned = str(raw)
            digits_only = "".join(ch for ch in cleaned if ch.isdigit())
            if not digits_only:
                continue
            base = digits_only.lstrip("0") or "0"
            candidates = [
                base,
                digits_only,
                base.zfill(3),
                base.zfill(4),
                base.zfill(5),
            ]
            seen = set()
            chosen = None
            for c in candidates:
                if c in seen:
                    continue
                seen.add(c)
                candidate_path = os.path.join(os.path.dirname(__file__), "..", "images", "Weapon_Images", f"weapon_{c}.jpg")
                if os.path.exists(candidate_path):
                    chosen = candidate_path
                    break
            if chosen:
                paths.append((chosen, _label.title()))
        return paths

    def _layout_preview_images(self, image_entries, max_w, max_h):
        """Place race image on the left, then weapons at the same height moving right."""
        if not image_entries:
            return
        target_height = max(max_h, 20)
        padding = 6
        pil_images = []

        for entry in image_entries:
            img = Image.open(entry["path"])
            img.thumbnail((max_w, target_height), Image.LANCZOS)
            pil_images.append((img, entry.get("label")))

        total_width = sum(img.width for img, _ in pil_images) + padding * (len(pil_images) - 1)
        if total_width > max_w and total_width > 0:
            scale = max_w / total_width
            scaled = []
            for img, label in pil_images:
                w = max(1, int(img.width * scale))
                h = max(1, int(img.height * scale))
                scaled.append((img.resize((w, h), Image.LANCZOS), label))
            pil_images = scaled

        y_offset = 0
        x = 4
        self.preview_renders = []
        for img, label in pil_images:
            photo = ImageTk.PhotoImage(img)
            self.preview_renders.append(photo)
            self.preview_canvas.create_image(x, y_offset, anchor="nw", image=photo, tags="preview_image")
            if label:
                self.preview_canvas.create_text(
                    x + (img.width // 2),
                    y_offset + img.height - 4,
                    text=label,
                    fill="#f0f0f0",
                    anchor="s",
                    font=("Arial", 8, "bold"),
                    tags="preview_label",
                )
            x += img.width + padding

    def _safe_int(self, value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _draw_preview_placeholder(self, message):
        """Show a subtle placeholder message on the preview canvas."""
        try:
            max_w = self.preview_canvas.winfo_width() or int(self.preview_canvas.cget("width"))
            max_h = self.preview_canvas.winfo_height() or int(self.preview_canvas.cget("height"))
        except Exception:
            max_w = max_h = 0
        x_offset = max((max_w - 200) // 2, 8)
        y_offset = max(max_h - 18, 8)
        self.preview_canvas.create_text(
            x_offset,
            y_offset,
            text=message,
            fill="#cfcfcf",
            anchor="nw",
            font=("Arial", 9, "italic"),
            tags="preview_text",
        )

    def _draw_preview_background(self, width, height, use_default=False):
        """Draw a dark background; optionally center the default logo when no preview image is available."""
        self.preview_canvas.create_rectangle(0, 0, width, height, fill="#2d2d2d", outline="#3c3c3c", tags="bg")
        if use_default and self.preview_bg_image:
            x_offset = max((width - self.preview_bg_image.width()) // 2, 0)
            y_offset = max((height - self.preview_bg_image.height()) // 2, 0)
            self.preview_canvas.create_image(x_offset, y_offset, anchor="nw", image=self.preview_bg_image, tags="bg")

    def _refresh_related_references(self):
        if not self.related_text:
            return
        sections = [
            self._get_loottable_summary_text(),
            self._get_faction_summary_text(),
        ]
        text = "\n\n".join([section for section in sections if section])
        if not text:
            text = "Linked data unavailable."
        self.related_text.configure(state="normal")
        self.related_text.delete("1.0", "end")
        self.related_text.insert("1.0", text)
        self.related_text.configure(state="disabled")

    def _get_loottable_summary_text(self):
        loottable_id = self._get_field_value("loottable_id")
        if not loottable_id:
            return "Loot Table: None assigned."
        if not str(loottable_id).isdigit():
            return f"Loot Table {loottable_id}: invalid ID."
        
        row = self._fetch_row(
            "SELECT id, name, avgcoin, mincash, maxcash FROM loottable WHERE id=%s",
            (loottable_id,),
        )
        if not row:
            return f"Loot Table {loottable_id}: not found."

        lines = [
            f"Loot Table {row.get('id')}: {row.get('name') or 'Unnamed'}",
            f"Avg Coin: {row.get('avgcoin')} | Cash Range: {row.get('mincash')} - {row.get('maxcash')}",
        ]

        lootdrops = self._fetch_rows(
            """
            SELECT lte.lootdrop_id, COALESCE(ld.name, '') AS lootdrop_name,
                   lte.multiplier, lte.mindrop, lte.droplimit, lte.probability
            FROM loottable_entries lte
            LEFT JOIN lootdrop ld ON lte.lootdrop_id = ld.id
            WHERE lte.loottable_id = %s
            ORDER BY lte.lootdrop_id
            """,
            (loottable_id,),
        )

        if lootdrops:
            print(f"[NPC Tool] Found {len(lootdrops)} lootdrops for table {loottable_id}")
            lines.append("Lootdrops:")
            for drop in lootdrops:
                drop_id = drop.get("lootdrop_id")
                name = drop.get("lootdrop_name") or "Unnamed"
                print(f"[NPC Tool] Processing lootdrop {drop_id} (type: {type(drop_id)})")
                lines.append(
                    f"  - {drop_id} ({name}) | Mult {drop.get('multiplier')} | "
                    f"Min {drop.get('mindrop')} | DropLimit {drop.get('droplimit')} | Chance {drop.get('probability')}"
                )
                
                # Convert drop_id to int to ensure type consistency
                drop_id_int = int(drop_id) if drop_id is not None else None
                if drop_id_int is None:
                    lines.append("      (Invalid lootdrop_id)")
                    continue
                
                print(f"[NPC Tool] Querying items for lootdrop_id: {drop_id_int}")
                item_rows = self._fetch_rows(
                    """
                    SELECT lde.item_id, COALESCE(i.Name, 'Unknown Item') AS item_name, 
                           lde.chance, lde.multiplier
                    FROM lootdrop_entries lde
                    LEFT JOIN items i ON lde.item_id = i.id
                    WHERE lde.lootdrop_id = %s
                    ORDER BY lde.item_id
                    """,
                    (drop_id_int,),
                )
                print(f"[NPC Tool] Found {len(item_rows)} items for lootdrop {drop_id_int}")
                print(f"[NPC Tool] Item data: {item_rows}")
                
                if not item_rows:
                    lines.append("      (No items linked)")
                    continue
                    
                for item in item_rows:
                    item_id = item.get("item_id")
                    # Try multiple possible column name variations
                    item_name = (item.get("item_name") or 
                                item.get("Name") or 
                                item.get("name") or 
                                "Unknown")
                    chance = item.get("chance", 0)
                    multiplier = item.get("multiplier", 1)
                    
                    lines.append(
                        f"      • Item {item_id}: {item_name} "
                        f"(Chance {chance}%, Mult {multiplier})"
                    )
        else:
            lines.append("Lootdrops: None linked.")

        return "\n".join(lines)

    def _get_faction_summary_text(self):
        faction_id = self._get_field_value("npc_faction_id")
        if not faction_id:
            return "Faction: None assigned."
        if not str(faction_id).isdigit():
            return f"Faction {faction_id}: invalid ID."
        row = self._fetch_row(
            "SELECT id, name FROM npc_faction WHERE id=%s",
            (faction_id,),
        )
        if not row:
            return f"Faction {faction_id}: not found."
        return f"Faction {row.get('id')}: {row.get('name') or 'Unnamed'} (use the Faction tool for relationships)"

    def _fetch_row(self, query, params):
        cursor = self.db_manager.get_cursor()
        if cursor is None:
            print("[NPC Tool] Failed to get cursor for _fetch_row")
            return None
        try:
            print(f"[NPC Tool] Executing query: {query}")
            print(f"[NPC Tool] With params: {params}")
            cursor.execute(query, params)
            result = cursor.fetchone()
            print(f"[NPC Tool] Query result: {result}")
            return result
        except Error as exc:
            self.set_status(f"Linked data error: {exc}")
            print(f"[NPC Tool] Database error in _fetch_row: {exc}")
            return None
        finally:
            cursor.close()

    def _fetch_rows(self, query, params):
        cursor = self.db_manager.get_cursor()
        if cursor is None:
            print("[NPC Tool] Failed to get cursor for _fetch_rows")
            return []
        try:
            print(f"[NPC Tool] Executing query: {query}")
            print(f"[NPC Tool] With params: {params}")
            cursor.execute(query, params)
            results = cursor.fetchall()
            print(f"[NPC Tool] Query returned {len(results)} rows")
            if results:
                print(f"[NPC Tool] First row: {results[0]}")
                print(f"[NPC Tool] First row keys: {results[0].keys() if hasattr(results[0], 'keys') else 'N/A'}")
            return results
        except Error as exc:
            self.set_status(f"Linked data error: {exc}")
            print(f"[NPC Tool] Database error in _fetch_rows: {exc}")
            return []
        finally:
            cursor.close()

    @staticmethod
    def _normalize_id(value):
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return value

    def clear_fields(self):
        for var in self.fields.values():
            if isinstance(var, tk.IntVar):
                var.set(0)
            elif isinstance(var, tk.StringVar):
                var.set("")
            elif isinstance(var, tk.Text):
                var.delete("1.0", "end")
        self._sync_special_fields_from_string("")
        self.npcid_var.set("")
        self.current_data = None
        self.save_button.config(state="disabled")
        self.set_status("Cleared form.")
        self._update_additional_tree_values()
        self._refresh_preview()
        self._refresh_related_references()

    def set_status(self, message):
        self.status_var.set(message)

    def _load_npc(self):
        npc_id = self.npcid_var.get().strip()
        if not npc_id.isdigit():
            messagebox.showwarning("Input", "Please enter a valid numeric NPC ID.")
            return
        self._load_npc_by_id(npc_id)

    def _load_npc_by_id(self, npc_id):
        npc_id = str(npc_id).strip()
        if not npc_id.isdigit():
            messagebox.showwarning("Input", "Please enter a valid numeric NPC ID.")
            return

        cursor = self.db_manager.get_cursor()
        if cursor is None:
            return
        try:
            cursor.execute("SELECT * FROM npc_types WHERE id = %s", (npc_id,))
            row = cursor.fetchone()
        except Error as e:
            messagebox.showerror("Database Error", str(e))
            row = None
        finally:
            cursor.close()

        if not row:
            messagebox.showinfo("Not Found", f"NPC ID {npc_id} not found.")
            self.save_button.config(state="disabled")
            return

        self.current_data = row
        self._set_fields_from_row(row)
        self.save_button.config(state="normal")
        self._refresh_preview()
        self._refresh_related_references()
        self.set_status(f"Loaded NPC {npc_id}")

    def _set_fields_from_row(self, row):
        for key, var in self.fields.items():
            if isinstance(var, tk.IntVar):
                try:
                    v = row.get(key, 0)
                    var.set(1 if str(v).strip() == "1" else 0)
                except Exception:
                    var.set(0)
            elif isinstance(var, tk.StringVar):
                val = row.get(key)
                var.set("" if val is None else str(val))
            elif isinstance(var, tk.Text):
                val = row.get(key)
                var.delete("1.0", "end")
                var.insert("1.0", "" if val is None else str(val))
        self._sync_special_fields_from_string(row.get("special_abilities", ""))
        self._update_additional_tree_values()

    def _get_row_from_fields(self):
        self._rebuild_special_abilities_string()
        row = {}
        for key, var in self.fields.items():
            if key.startswith("sa_"):
                continue
            if isinstance(var, tk.IntVar):
                row[key] = var.get()
            elif isinstance(var, tk.StringVar):
                row[key] = var.get()
            elif isinstance(var, tk.Text):
                row[key] = var.get("1.0", "end-1c")
        return row

    def _get_field_value(self, key):
        var = self.fields.get(key)
        if isinstance(var, tk.IntVar):
            return var.get()
        if isinstance(var, tk.StringVar):
            return var.get().strip()
        if isinstance(var, tk.Text):
            return var.get("1.0", "end-1c").strip()
        return ""

    def _create_npc(self):
        row = self._get_row_from_fields()
        npc_id = row.get("id")
        if not npc_id or not str(npc_id).isdigit():
            messagebox.showwarning("Create NPC", "A valid numeric ID is required to create a new NPC.")
            return

        cursor = self.db_manager.get_cursor()
        if cursor is None:
            return
        try:
            cursor.execute("SELECT id FROM npc_types WHERE id=%s", (npc_id,))
            if cursor.fetchone():
                messagebox.showerror("Create NPC", f"NPC ID {npc_id} already exists.")
                return
        except Error as e:
            messagebox.showerror("Database Error", str(e))
            return
        finally:
            cursor.close()

        columns = []
        values = []
        for key, value in row.items():
            field = self.fields.get(key)
            if key == "id":
                columns.append(key)
                values.append(value)
                continue
            if isinstance(field, tk.IntVar):
                columns.append(key)
                values.append(value)
                continue
            if value is None:
                continue
            if isinstance(value, str):
                value = value.strip()
                if value == "":
                    continue
            columns.append(key)
            values.append(value)

        if not columns:
            messagebox.showwarning("Create NPC", "No values were provided to create an NPC.")
            return

        placeholders = ", ".join(["%s"] * len(columns))
        column_list = ", ".join(columns)

        cursor = self.db_manager.get_cursor(dictionary=False)
        if cursor is None:
            return
        conn = self.db_manager.connect()
        try:
            cursor.execute(f"INSERT INTO npc_types ({column_list}) VALUES ({placeholders})", values)
            conn.commit()
        except Error as e:
            messagebox.showerror("Database Error", str(e))
            conn.rollback()
            return
        finally:
            cursor.close()

        self.set_status(f"Created NPC {npc_id}")
        messagebox.showinfo("Created", f"NPC {npc_id} created.")
        self._load_npc_by_id(npc_id)

    def _save_npc(self):
        row = self._get_row_from_fields()
        npc_id = row.get("id")
        if not npc_id:
            messagebox.showwarning("ID", "ID field is required.")
            return

        keys = [k for k in row.keys() if k != "id"]
        if not keys:
            messagebox.showwarning("No Changes", "No editable fields were found.")
            return

        sets = ", ".join(f"{k}=%s" for k in keys)
        values = [row[k] for k in keys]
        values.append(npc_id)

        cursor = self.db_manager.get_cursor(dictionary=False)
        if cursor is None:
            return
        conn = self.db_manager.connect()
        try:
            cursor.execute(f"UPDATE npc_types SET {sets} WHERE id=%s", values)
            conn.commit()
        except Error as e:
            messagebox.showerror("Database Error", str(e))
            conn.rollback()
            return
        finally:
            cursor.close()

        self._refresh_preview()
        self._refresh_related_references()
        self.set_status(f"Saved NPC {npc_id}")
        messagebox.showinfo("Saved", f"NPC {npc_id} saved.")
