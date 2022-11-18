from dataclasses import dataclass

from seedwork.application.commands import Command
from seedwork.domain.value_objects import UUID, Money
from seedwork.application.command_handlers import CommandResult
from seedwork.application.decorators import command_handler
from modules.catalog.domain.entities import Listing
from modules.catalog.domain.events import ListingDraftCreatedEvent
from modules.catalog.domain.repositories import ListingRepository


@dataclass
class CreateListingDraftCommand(Command):
    """A command for creating new listing in draft state"""

    title: str
    description: str
    ask_price: Money
    seller_id: UUID


@command_handler
def create_listing_draft(
    command: CreateListingDraftCommand, repository: ListingRepository
) -> CommandResult:
    listing = Listing(
        id=Listing.next_id(),
        title=command.title,
        description=command.description,
        ask_price=command.ask_price,
        seller_id=command.seller_id,
    )
    repository.add(listing)
    return CommandResult.ok(
        result=listing.id, events=[ListingDraftCreatedEvent(listing_id=listing.id)]
    )
