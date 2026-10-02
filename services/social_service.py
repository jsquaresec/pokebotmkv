from sqlalchemy import or_, select
from models.friendship import Friendship


class SocialService:
    def __init__(self, session):
        self.session = session

    async def request(self, requester: int, addressee: int):
        if requester == addressee:
            raise ValueError("You cannot add yourself.")
        stmt = (
            select(Friendship)
            .where(
                or_(
                    (Friendship.requester_discord_id == requester) & (Friendship.addressee_discord_id == addressee),
                    (Friendship.requester_discord_id == addressee) & (Friendship.addressee_discord_id == requester),
                )
            )
            .with_for_update()
        )
        if (await self.session.execute(stmt)).scalar_one_or_none():
            raise ValueError("A friendship or request already exists.")
        row = Friendship(requester_discord_id=requester, addressee_discord_id=addressee)
        self.session.add(row)
        await self.session.flush()
        return row

    async def accept(self, addressee: int, request_id: int):
        row = (
            await self.session.execute(select(Friendship).where(Friendship.id == request_id).with_for_update())
        ).scalar_one_or_none()
        if not row or row.addressee_discord_id != addressee or row.status != "pending":
            raise ValueError("Pending friend request not found.")
        row.status = "accepted"
        await self.session.flush()
        return row

    async def list_friends(self, discord_id: int):
        stmt = select(Friendship).where(
            Friendship.status == "accepted",
            or_(Friendship.requester_discord_id == discord_id, Friendship.addressee_discord_id == discord_id),
        )
        rows = list((await self.session.execute(stmt)).scalars().all())
        return [
            r.addressee_discord_id if r.requester_discord_id == discord_id else r.requester_discord_id for r in rows
        ]
