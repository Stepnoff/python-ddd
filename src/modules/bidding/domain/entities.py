from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import List, Optional
from collections.abc import Sequence
from modules.bidding.domain.value_objects import Bid, Bidder, Seller
from modules.bidding.domain.rules import (
    PlacedBidMustBeGreaterThanCurrentWinningBid,
    BidCanBeRetracted,
)
from seedwork.domain.entities import AggregateRoot
from seedwork.domain.events import DomainEvent
from seedwork.domain.exceptions import DomainException
from seedwork.domain.events import DomainEvent
from seedwork.domain.value_objects import UUID, Money


class BidderIsNotBiddingListing(DomainException):
    ...


class BidCannotBeRetracted(DomainException):
    ...


class ListingCannotBeCancelled(DomainException):
    ...


class BidPlacedEvent(DomainEvent):
    ...


class BidRetractedEvent(DomainEvent):
    ...


class ListingCancelledEvent(DomainEvent):
    ...


@dataclass(kw_only=True)
class Listing(AggregateRoot):
    seller: Seller
    initial_price: Money
    ends_at: datetime
    bids: List[Bid] = field(default_factory=list)
    current_price: Money = field(init=False)

    def __post_init__(self) -> None:
        self.current_price = self.initial_price

    # public commands
    def place_bid(self, bid: Bid) -> Sequence[DomainEvent]:
        """Public method"""
        self.check_rule(
            PlacedBidMustBeGreaterThanCurrentWinningBid(
                bid=bid, current_price=self.current_price
            )
        )

        if self.has_bid_placed_by(bidder=bid.bidder):
            self._update_bid(bid)
        else:
            self._add_bid(bid)

        return [BidPlacedEvent(listing_id=self.id, bidder=bid.bidder, price=bid.price)]

    def retract_bid_of(self, bidder: Bidder) -> Sequence[DomainEvent]:
        """Public method"""
        bid = self.get_bid_of(bidder)
        self.check_rule(
            BidCanBeRetracted(listing_ends_at=self.ends_at, bid_placed_at=bid.placed_at)
        )

        self._remove_bid_of(bidder=bidder)
        return [BidRetractedEvent(listing_id=self.id, bidder_id=bidder.uuid)]

    def cancel_listing(self) -> Sequence[DomainEvent]:
        raise NotImplementedError()

    def end_bidding(self) -> Sequence[DomainEvent]:
        raise NotImplementedError()

    # public queries
    def get_bid_of(self, bidder: Bidder) -> Bid:
        try:
            bid = next(filter(lambda bid: bid.bidder == bidder, self.bids))
        except StopIteration as e:
            raise BidderIsNotBiddingListing() from e
        return bid

    def has_bid_placed_by(self, bidder: Bidder) -> bool:
        try:
            self.get_bid_of(bidder=bidder)
        except BidderIsNotBiddingListing:
            return False
        return True

    @property
    def winning_bid(self) -> Optional[Bid]:
        try:
            highest_bid = max(self.bids, key=lambda bid: bid.price)
        except ValueError:
            # nobody is bidding
            return None
        return highest_bid

    # private commands and queries
    def _add_bid(self, bid: Bid):
        assert not self.has_bid_placed_by(
            bidder=bid.bidder
        ), "Only one bid of a bidder is allowed"
        self.bids.append(bid)

    def _update_bid(self, bid: Bid):
        self.bids = [
            bid if bid.bidder == existing.bidder else existing for existing in self.bids
        ]
