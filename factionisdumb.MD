Faction Standing = base + R/C/D + action hits + association spillover, then clamp to min/max range.

NPCs don’t point to factions; they point to groups.

Groups decide behavior (assist/neutral/hostile) and action hits.


Make a Faction
Set name + base.
Add clamps (min/max).
Add Race/Class/Deity modifiers if needed.
Link Factions (optional)
Add up to 5 associations w/ modifiers

Make a Group (NPC policy, Dragons, Tunare)
Add entries (one per relevant faction):
Faction Hit: how much an action changes standing.
NPC Reaction: 1=Assist, 0=Neutral, -1=Hostile.  If your npc has npc_aggro = 1 it will attack other NPCs it is hostile to.
Temporary: 1 if you don’t want that faction hit to persist.
Assign Group to NPCs
Set NPC’s faction group id. Done.


groups and associations solve different problems.

When to use a group entry

Local, action policy: Defines “what changes when this NPC/group is involved.”
Per-NPC reuse: Many NPCs share the same hit/reaction rules without duplicating rows.
Context-bound: Only fires when the action goes through that group (e.g., kill/assist that NPC).

When to use an association

Global coupling: “If A goes up, B should always go down,” regardless of where the gain came from.
Works without group context: Quest turn-ins, scripts, GM commands, or any standing change that adjusts a single faction still propagates to linked ones.
Consistency across groups: Avoids duplicating the same “A vs B vs C” math in multiple groups.
Conflict reduction: Putting the same related factions in multiple groups invites contradictory hits or double-counting. Associations keep the relationship math centralized and predictable.
Maintenance: Adjust one weight instead of hunting multiple groups to tweak balance.

Group entries = where the immediate change is defined (what this NPC/group does).
Associations = how changes ripple to other factions everywhere (global relationship).