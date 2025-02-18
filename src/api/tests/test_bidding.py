import pytest

from modules.catalog.application.command import (
    CreateListingDraftCommand,
    PublishListingDraftCommand,
)
from seedwork.domain.value_objects import GenericUUID, Money
from seedwork.infrastructure.logging import logger


async def setup_app_for_bidding_tests(app, listing_id, seller_id, bidder_id):
    logger.info("Adding users")
    with app.transaction_context() as ctx:
        iam_service = ctx["iam_service"]

        iam_service.create_user(
            user_id=seller_id,
            email="seller@example.com",
            password="password",
            access_token="token1",
        )
        ctx["logger"].debug(f"Added seller: {seller_id}")

        iam_service.create_user(
            user_id=bidder_id,
            email="bidder@example.com",
            password="password",
            access_token="token2",
        )
        ctx["logger"].debug(f"Added bidder: {bidder_id}")

    await app.execute_async(
        CreateListingDraftCommand(
            listing_id=listing_id,
            title="Foo",
            description="Bar",
            ask_price=Money(10),
            seller_id=seller_id,
        )
    )
    logger.info(f"Created listing draft: {listing_id}")

    await app.execute_async(
        PublishListingDraftCommand(listing_id=listing_id, seller_id=seller_id)
    )
    logger.info(f"Published listing draft {listing_id} by seller {seller_id}")

    logger.info("test setup complete")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_place_bid(app, api_client):
    listing_id = GenericUUID(int=1)
    seller_id = GenericUUID(int=2)
    bidder_id = GenericUUID(int=3)
    await setup_app_for_bidding_tests(app, listing_id, seller_id, bidder_id)

    url = f"/bidding/{listing_id}/place_bid"

    response = api_client.post(url, json={"bidder_id": str(bidder_id), "amount": 11})
    json = response.json()
    assert response.status_code == 200
