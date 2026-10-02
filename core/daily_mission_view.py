from core.game_gui import ResultView, gui_send, gui_defer, card
from core.database import SessionLocal
from services.daily_mission_service import DailyMissionService, MISSIONS


def item_name(sku):
    return sku.replace('_', ' ').title().replace('Poke Ball', 'Poké Ball')


async def show_missions(interaction, notice='', tier='easy'):
    await gui_defer(interaction)
    async with SessionLocal() as session:
        try:
            rows = await DailyMissionService(session).board(interaction.user.id)
            await session.commit()
        except ValueError as exc:
            await gui_send(interaction, str(exc), ephemeral=True)
            return
        lines = [notice] if notice else []
        view = ResultView(interaction.user.id)
        for difficulty in ('easy', 'medium', 'hard'):
            async def switch(click, selected=difficulty):
                await show_missions(click, tier=selected)
            view.button(difficulty.title(), switch, disabled=difficulty == tier)
        for row in rows:
            mission = MISSIONS[row.code]
            if mission['tier'] != tier:
                continue
            target = mission['target']
            status = 'Claimed' if row.claimed_at else ('Ready to claim' if row.progress >= target else 'In progress')
            lines.append(f'**{mission['label']}** — {row.progress}/{target} · {status}\nReward: **{row.reward_quantity} × {item_name(row.reward_sku)}**')
            async def claim(click, code=row.code, day=row.day):
                await gui_defer(click)
                async with SessionLocal() as claim_session:
                    try:
                        reward = await DailyMissionService(claim_session).claim(click.user.id, code, day)
                        message = f'Added **{reward.reward_quantity} × {item_name(reward.reward_sku)}** to your inventory!'
                        await claim_session.commit()
                    except ValueError as exc:
                        message = str(exc)
                await show_missions(click, message, tier)
            view.button(f'Claim: {mission['label']}', claim,
                        disabled=row.progress < target or row.claimed_at is not None)
        lines.append('Resets at midnight UTC. Unclaimed rewards expire at reset.')
        await gui_send(interaction, embed=card(f'Daily Missions — {tier.title()}', '\n\n'.join(lines)), view=view, ephemeral=True)

