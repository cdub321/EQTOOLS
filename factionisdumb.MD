- The 'npc_faction' column in the "npc_types" table does NOT point to a faction directly. It points to a faction GROUP.
- A faction score is tied to "faction_list.id" (one row per faction).

How a faction score is calculated (real columns)

Score = base value
      + race/class/deity modifiers
      + hits from actions (kills, quests, etc.)
      + association spillover (other factions linked to this one)
Then it is clamped between min and max.

Where the numbers live:
- Base value: "faction_list.base" for the faction.
- Clamp: "faction_base_data.min" and "faction_base_data.max" for the faction
  (row keyed by "faction_base_data.client_faction_id = faction_list.id").
- Race/Class/Deity modifiers: "faction_list_mod" rows for the faction
  ("faction_list_mod.faction_id", "mod_name", "mod").
- Association spillover: "faction_association" row where "id" = this faction and
  "id_1..id_5/mod_1..mod_5" link to other factions.

What is a faction GROUP? (real tables/columns)

A group is a row in "npc_faction".
NPCs use it via "npc_types.npc_faction_id" = "npc_faction.id".

A group has entries in "npc_faction_entries". Each entry says:
- Faction Hit: "npc_faction_entries.value"
- NPC Reaction: "npc_faction_entries.npc_value" (1=Assist, 0=Neutral, -1=Hostile)
- Temporary: "npc_faction_entries.temp" (1 = do not persist)

Cause and effect:
- If an NPC has "npc_types.npc_faction_id = 123", the tool loads group 123 from "npc_faction".
- When that NPC is involved in an action, the rows in "npc_faction_entries" with
  "npc_faction_id = 123" decide which factions get hit and how the NPC reacts.

Make a faction (step-by-step with DB columns)
1) Set name and base value.
   - "faction_list.id", "faction_list.name", "faction_list.base"
2) Set min/max clamp.
   - "faction_base_data.client_faction_id", "min", "max"
3) Add race/class/deity modifiers if you need them.
   - "faction_list_mod.faction_id", "mod_name", "mod"
4) (Optional) Add associations (up to 5).
   - "faction_association.id" and "id_1..id_5/mod_1..mod_5"

Make a group (step-by-step with DB columns)
1) Create the group (npc_faction row).
   - "npc_faction.id", "npc_faction.name", "npc_faction.primaryfaction"
2) Add entries for each relevant faction.
   - "npc_faction_entries.npc_faction_id", "faction_id", "value", "npc_value", "temp"
3) Assign the group ID to NPCs.
   - "npc_types.npc_faction_id"

Groups vs associations (short version)

Use GROUP entries when:
- The change depends on which NPC you interacted with.
- You want multiple NPCs to share the same hit/reaction rules.

Use ASSOCIATIONS when:
- You always want gains/losses in one faction to spill into another.
- The change should happen no matter where the faction change came from
  (quests, scripts, GM commands, kills, etc.).

One-liners
- Group entries = "what this NPC/group does to faction when involved."
- Associations = "global links between factions that always ripple."

Concrete example (follow the IDs)
1) NPC "a_guard" has "npc_types.id = 2001" and "npc_types.npc_faction_id = 300".
2) Group 300 exists in "npc_faction.id = 300".
3) Group 300 has entries:
   - "npc_faction_entries.npc_faction_id = 300, faction_id = 500, value = -10, npc_value = -1"
4) Faction 500 exists in "faction_list.id = 500".
5) Result:
   - When you kill/help that guard, faction 500 changes by -10 (value),
     and the NPC reacts as hostile (npc_value = -1) for that group.
