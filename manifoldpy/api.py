"""API bindings"""
import bisect
import sys
from time import time
from typing import Any, Dict, List, Literal, Mapping, Optional, Tuple, Type, TypeVar

import numpy as np
import numpy.typing as npt
import requests
from attr import define, field

from manifoldpy import config

V0_URL = "https://api.manifold.markets/v0/"

# GET URLs

ALL_MARKETS_URL = V0_URL + "markets"
SEARCH_MARKETS_URL = V0_URL + "search-markets"
BETS_URL = V0_URL + "bets"
COMMENTS_URL = V0_URL + "comments"
GROUPS_URL = V0_URL + "groups"
GROUP_SLUG_URL = V0_URL + "group/{group_slug}"
GROUP_ID_URL = V0_URL + "group/by-id/{group_id}"
GROUP_MARKETS_URL = V0_URL + "group/by-id/{group_id}/markets"
ME_URL = V0_URL + "me"
MARKET_SLUG_URL = V0_URL + "slug/{}"
SINGLE_MARKET_URL = V0_URL + "market/{}"
POSITION_URL = V0_URL + "market/{}/positions"
USERNAME_URL = V0_URL + "user/{}"
USER_ID_URL = V0_URL + "user/by-id/{}"
USERS_URL = V0_URL + "users"


# POST URLs
MAKE_BET_URL = V0_URL + "bet"
CANCEL_BET_URL = V0_URL + "bet/cancel/{}"
CREATE_MARKET_URL = V0_URL + "market"
ADD_LIQUIDITY_URL = V0_URL + "market/{}/add-liquidity"
CLOSE_URL = V0_URL + "market/{}/close"
RESOLVE_MARKET_URL = V0_URL + "market/{}/resolve"
SELL_SHARES_URL = V0_URL + "market/{}/sell"
MAKE_COMMENT_URL = V0_URL + "comment"


MarketT = TypeVar("MarketT", bound="Market")
OutcomeType = Literal[
    "BINARY", "FREE_RESPONSE", "PSEUDO_NUMERIC", "MULTIPLE_CHOICE", "NUMERIC"
]
OrderType = Literal["shares", "profit"]
Visibility = Literal["public", "unlisted"]
T = TypeVar("T")


def weak_structure(json: dict, cls: Type[T]) -> T:
    fields = {}
    for f in cls.__attrs_attrs__:  # type: ignore
        val = json.get(f.name, f.default)
        fields[f.name] = val
    return cls(**fields)  # type: ignore


def _maybe_unstructure(val: Any) -> Any:
    if hasattr(val, "__attrs_attrs__"):
        return weak_unstructure(val)
    elif isinstance(val, list):
        return [_maybe_unstructure(v) for v in val]
    else:
        return val


def weak_unstructure(obj: Any) -> Dict[str, Any]:
    """Convert an attrs class to a dict."""
    d = {}
    for f in obj.__attrs_attrs__:
        key = f.name
        val = getattr(obj, key)
        # if hasattr(val, "__attrs_attrs__"):
        #     val = weak_unstructure(val)
        # elif isinstance(val, list):
        #     val = [weak_unstructure(v) for v in val]
        d[key] = _maybe_unstructure(val)

    return d


@define
class Answer:
    """An answer to a free response market"""


@define
class Bet:
    """A single bet"""

    contractId: str
    createdTime: int
    shares: float
    amount: int
    probAfter: float
    probBefore: float
    id: str
    outcome: str
    challengeSlug: Optional[str] = None
    isLiquidityProvision: Optional[bool] = None
    isCancelled: Optional[bool] = None
    orderAmount: Optional[float] = None
    fills: Optional[float] = None
    isFilled: Optional[bool] = None
    limitProb: Optional[float] = None
    dpmShares: Optional[float] = None
    # TODO: Define Fees class
    fees: Optional[dict] = None
    # TODO: Define Sale class
    sale: Optional[dict] = None
    isSold: Optional[bool] = None
    loanAmount: Optional[float] = None
    isRedemption: Optional[bool] = None
    isAnte: Optional[bool] = None
    userId: Optional[str] = None


@define
class Comment:
    """A comment on a market"""

    id: str
    commentId: str
    contractId: str
    contractQuestion: str
    userUsername: str
    userAvatarUrl: str
    userId: str
    createdTime: int
    userName: str
    content: str
    commentType: str
    contractSlug: str
    visibility: bool
    isApi: bool
    betId: Optional[str] = None
    betAmount: Optional[float] = None
    betOutcome: Optional[Any] = None
    commenterPositionOutcome: Optional[Any] = None
    replyToCommentId: Optional[str] = None
    likes: Optional[int] = None
    commenterPositionShares: Optional[float] = None
    commenterPositionProb: Optional[float] = None
    answerOutcome: Optional[str] = None
    hiderId: Optional[str] = None
    hidden: Optional[bool] = None
    hiddenTime: Optional[int] = None
    bettorName: Optional[str] = None
    bettorUsername: Optional[str] = None
    editedTime: Optional[int] = None
    betAnswerId: Optional[str] = None
    commenterPositionAnswerId: Optional[str] = None
    bountyAwarded: Optional[bool] = None
    betReplyAmountsByOutcome: Optional[Dict[str, int]] = None


@define
class Group:
    """ "A Manifold group
    Note that tags count as groups.
    """

    mostRecentActivityTime: int
    aboutPostId: str
    creatorId: str
    mostRecentContractAddedTime: int
    anyoneCanJoin: bool
    name: str
    totalMembers: int
    createdTime: int
    about: str
    slug: str
    id: str
    totalContracts: Any
    cachedLeaderboard: Dict[str, Any]
    pinnedItems: List[Any]


@define
class User:
    """A manifold user"""

    id: str
    createdTime: int
    name: str
    username: str
    url: str
    avatarUrl: str
    balance: float
    totalDeposits: float
    profitCached: Dict[str, Optional[float]]
    creatorVolumeCached: Dict[str, float]
    bio: Optional[str] = None
    twitterHandle: Optional[str] = None
    discordHandle: Optional[str] = None
    bannerUrl: Optional[str] = None
    website: Optional[str] = None


@define
class Market:
    """A market"""

    id: str
    creatorUsername: str
    creatorName: str
    createdTime: int
    question: str
    url: str
    slug: str
    pool: Dict[str, float]
    volume: float
    volume24Hours: float
    outcomeType: OutcomeType
    mechanism: str
    isResolved: bool
    lastUpdatedTime: int
    closeTime: int
    creatorId: str
    creatorAvatarUrl: str
    uniqueBettorCount: int
    resolutionProbability: Optional[float] = field(kw_only=True, default=None)
    resolverId: Optional[str] = field(kw_only=True, default=None)
    p: Optional[float] = field(kw_only=True, default=None)
    totalLiquidity: Optional[float] = field(kw_only=True, default=None)
    resolution: Optional[str] = field(kw_only=True, default=None)
    resolutionTime: Optional[int] = field(kw_only=True, default=None)
    lastBetTime: Optional[float] = field(kw_only=True, default=None)
    lastCommentTime: Optional[int] = field(kw_only=True, default=None)
    min: Optional[int] = field(kw_only=True, default=None)
    max: Optional[int] = field(kw_only=True, default=None)
    isLogScale: Optional[bool] = field(kw_only=True, default=None)
    # Separating into Lite and Full market types would be pointlessly annoying
    textDescription: Optional[str] = field(kw_only=True, default=None)
    description: Optional[dict] = field(kw_only=True, default=None)
    bets: Optional[List[Bet]] = field(kw_only=True, default=None)
    comments: Optional[List[Comment]] = field(kw_only=True, default=None)
    
    def get_full_data(self) -> "Market":
        self.bets = get_bets(marketId=self.id)
        self.comments = get_comments(marketId=self.id)
        return self

    def get_updates(self) -> Tuple[np.ndarray, np.ndarray]:  # pragma: no cover
        """Get all updates to this market.

        Returns:
            Tuple[np.ndarray, np.ndarray]: The time of each update, and the probabilities after each update.
        """
        raise NotImplementedError

    def num_traders(self) -> int:  # pragma: no cover
        raise NotImplementedError

    def probability_history(self) -> Tuple[np.ndarray, np.ndarray]:  # pragma: no cover
        raise NotImplementedError

    def start_probability(self) -> float:  # pragma: no cover
        """Get the starting probability of the market"""
        raise NotImplementedError

    def final_probability(self) -> float:  # pragma: no cover
        """Get the final probability of this market"""
        raise NotImplementedError

    @staticmethod
    def from_json(json: Any) -> "Market":
        if "bets" in json and json["bets"] is not None:
            json["bets"] = [weak_structure(x, Bet) for x in json["bets"]]
        if "comments" in json and json["comments"] is not None:
            json["comments"] = [weak_structure(x, Comment) for x in json["comments"]]

        try:
            cls = MARKET_TYPES_MAP[json["outcomeType"]]
        except KeyError:
            market_id = json["id"]
            raise ValueError(
                f'{json["outcomeType"]} isn\'t a known market outcome type. Submit a bug report for market ID {market_id}.'
            )
        return weak_structure(json, cls)


@define
class BinaryMarket(Market):
    """A market with a binary resolution"""

    probability: float

    def num_traders(self) -> int:
        if self.bets is None:
            return 0
        else:
            unique_traders = {b.userId for b in self.bets}
            return len(unique_traders)

    def probability_history(
        self,
    ) -> Tuple[npt.NDArray[np.int_], npt.NDArray[np.float_]]:
        assert (
            self.bets is not None
        ), "Call get_market before accessing probability history"
        times: npt.NDArray[np.int_]
        probabilities: npt.NDArray[np.float_]
        if len(self.bets) == 0:
            times, probabilities = np.array([self.createdTime]), np.array(
                [self.probability]
            )
        else:
            s_bets = sorted(self.bets, key=lambda x: x.createdTime)
            start_prob = s_bets[0].probBefore
            start_time = self.createdTime
            t_iter, p_iter = zip(*[(bet.createdTime, bet.probAfter) for bet in s_bets])
            times, probabilities = np.array((start_time, *t_iter)), np.array(
                (start_prob, *p_iter)
            )
        return times, probabilities

    def start_probability(self) -> float:
        return self.probability_history()[1][0]

    def final_probability(self) -> float:
        return self.probability_history()[1][-1]

    def probability_at_time(self, timestamp: float):
        times, probs = self.probability_history()
        if timestamp < times[0]:
            raise ValueError(f"Timestamp {timestamp} before market creation {times[0]}")
        else:
            index = bisect.bisect(times, timestamp)
            assert index > 0  # should be caught above
            return probs[index - 1]


@define
class FreeResponseMarket(Market):
    """A market with multiple possible resolutions"""

    answers: Optional[List[Any]] = None

    def outcome_history(self) -> Tuple[Tuple[str, ...], np.ndarray]:
        assert self.answers is not None
        outcomes, times = zip(*[(a["text"], a["createdTime"]) for a in self.answers])
        return outcomes, np.array(times)

    def full_history(self) -> Tuple[np.ndarray, np.ndarray]:
        assert (
            self.bets is not None
        ), "Can't get history. Need to download bet history first."
        self.bets = sorted(self.bets, key=lambda x: x.createdTime)
        outcomes, _ = self.outcome_history()
        amounts = np.zeros((len(outcomes) + 1, len(self.bets)))
        times = np.empty(len(self.bets), dtype=int)
        for i, b in enumerate(self.bets):
            idx = int(b.outcome)
            amounts[idx, i] = b.shares
            times[i] = b.createdTime
        total_invested = amounts.cumsum(axis=1)
        squared_invested = total_invested**2
        squared_pool = squared_invested.sum(axis=0)
        probabilities = squared_invested / squared_pool

        return times, probabilities

    def probability_history(self) -> Tuple[np.ndarray, np.ndarray]:
        assert self.resolution is not None
        times, probabilities = self.full_history()
        resolution = int(self.resolution)
        return times, probabilities[resolution]

    def final_probability(self) -> float:
        if self.bets is None:
            pass
        raise NotImplementedError


@define
class NumericMarket(Market):
    pass


@define
class PseudoNumericMarket(Market):
    value: float
    probability: float


@define
class MultipleChoiceMarket(Market):
    answers: List[dict]
    def outcome_history(self) -> Tuple[Tuple[str, ...], np.ndarray]:
        assert self.answers is not None
        outcomes, times = zip(*[(a["text"], a["createdTime"]) for a in self.answers])
        return outcomes, np.array(times)

    def full_history(self) -> Tuple[np.ndarray, np.ndarray]:
        assert (
            self.bets is not None
        ), "Can't get history. Need to download bet history first."
        if len(self.bets) == 0:
            _, itr_probs,itr_times = zip(*sorted([(answer["index"],answer["probability"],answer["createdTime"]) for answer in self.answers]))
            probabilities=np.array(itr_probs)[:,np.newaxis]
            times=np.unique(itr_times)

        else:
            s_bets = sorted(self.bets, key=lambda x: x.createdTime,reverse=True)
            outcomes, _ = self.outcome_history()
            start_time=self.createdTime
            times=np.unique((start_time,*[int(bet.createdTime) for bet in self.bets] ))
            probabilities=np.empty((len(outcomes) , times.shape[0] ))
            probabilities.fill(np.nan)
            initual_prob=np.zeros((len(outcomes) ))
            id_to_index=dict([(answer["id"],answer["index"]) for answer in self.answers])
            for bet in s_bets:
                i=np.argwhere(times == bet.createdTime)[0][0]
                idx = int(id_to_index[bet.answerId])
                probabilities[idx, i] = bet.probAfter
                initual_prob[idx]=bet.probBefore
            probabilities[:,0]=initual_prob
            mask = np.isnan(probabilities)
            idx = np.where(~mask,np.arange(mask.shape[1]),0)
            _ = np.maximum.accumulate(idx,axis=1, out=idx)
            probabilities[mask] = probabilities[np.nonzero(mask)[0], idx[mask]]

        return times, probabilities


    def probability_history(self) -> Tuple[np.ndarray, np.ndarray]:
        assert self.resolution is not None
        id_to_index=dict([(answer["id"],answer["index"]) for answer in self.answers])
        times, probabilities = self.full_history()
        resolution = id_to_index[self.resolution]
        return times, probabilities[resolution]

@define
class QuadraticFundingMarket(Market):
    pass


@define
class StonkMarket(Market):
    """Don't ask me what they were thinking with this name"""

    pass


@define
class Poll(Market):
    pass


@define
class BountiedMarket(Market):
    pass


@define
class ContractMetric:
    contractId: str
    from_dict: dict
    hasNoShares: bool
    hasShares: bool
    hasYesShares: bool
    invested: float
    loan: float
    maxSharesOutcome: Optional[str]
    payout: float
    profit: float
    profitPercent: float
    totalShares: dict
    userId: str
    userUsername: str
    userName: str
    userAvatarUrl: str
    lastBetTime: float

    @classmethod
    def from_json(cls, json_dict: dict) -> "ContractMetric":
        if "from" in json_dict:
            json_dict["from_dict"] = json_dict["from"]
            del json_dict["from"]
        return weak_structure(json_dict, cls)


MARKET_TYPES_MAP: Mapping[str, Type[Market]] = {
    "BINARY": BinaryMarket,
    "FREE_RESPONSE": FreeResponseMarket,
    "NUMERIC": NumericMarket,
    "PSEUDO_NUMERIC": PseudoNumericMarket,
    "MULTIPLE_CHOICE": MultipleChoiceMarket,
    "QUADRATIC_FUNDING": QuadraticFundingMarket,
    "STONK": StonkMarket,
    "POLL": Poll,
    "BOUNTIED_QUESTION": BountiedMarket,
}


def _get_bets(
    userId: Optional[str] = None,
    username: Optional[str] = None,
    marketId: Optional[str] = None,
    marketSlug: Optional[str] = None,
    limit: Optional[int] = 1000,
    before: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get bets, optionally associated with a user or market.
    Retrieves at most 1000 bets.
    [API reference](https://docs.manifold.markets/api#get-v0bets)

    Args:
        userId: ID of user to get bets for.
        username: Username of user to get bets for.
        marketId: The market to get bets for.
        marketSlug: Slug of the market to get bets for
        limit: Number of bets to return. Maximum 1000.
        before: ID of a bet to fetch bets before.
    """
    params: Dict[str, Any] = {"limit": limit}
    if userId is not None:
        params["userId"] = userId
    if username is not None:
        params["username"] = username
    if marketId is not None:
        params["contractId"] = marketId
    if marketSlug is not None:
        params["contractSlug"] = marketSlug
    if limit is not None:
        params["limit"] = limit
    if before is not None:
        params["before"] = before
    resp = requests.get(BETS_URL, params=params)
    resp.raise_for_status()

    unsorted = resp.json()
    return sorted(unsorted, key=lambda x: x["createdTime"], reverse=True)


def get_bets(
    userId: Optional[str] = None,
    username: Optional[str] = None,
    marketId: Optional[str] = None,
    marketSlug: Optional[str] = None,
    limit: Optional[int] = 1000,
    before: Optional[str] = None,
) -> List[Bet]:
    """Get bets, optionally associated with a user or market.
    Retrieves at most 1000 bets.
    [API reference](https://docs.manifold.markets/api#get-v0bets)

    Args:
        userId: ID of user to get bets for.
        username: Username of user to get bets for.
        marketId: The market to get bets for.
        marketSlug: Slug of the market to get bets for
        limit: Number of bets to return. Maximum 1000.
        before: ID of a bet to fetch bets before.
        as_json: If true, return the raw json instead of a list of Bet objects.
    """
    return [
        weak_structure(x, Bet)
        for x in _get_bets(
            userId=userId,
            username=username,
            marketId=marketId,
            marketSlug=marketSlug,
            limit=limit,
            before=before,
        )
    ]


def _get_all_bets(
    username: Optional[str] = None,
    userId: Optional[str] = None,
    marketId: Optional[str] = None,
    marketSlug: Optional[str] = None,
    after: int = 0,
    limit: int = sys.maxsize,
    before_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Underlying API call for `get_all_bets`."""
    bets: List[Dict[str, Any]] = []
    i = before_id
    while True:
        num_to_get = min(limit - len(bets), 1000)
        if num_to_get <= 0:
            break
        new_bets = [
            b
            for b in _get_bets(
                limit=num_to_get,
                before=i,
                username=username,
                userId=userId,
                marketId=marketId,
                marketSlug=marketSlug,
            )
            if b["createdTime"] > after
        ]
        bets.extend(new_bets)
        print(f"Fetched {len(bets)} bets.")
        if len(new_bets) < 1000:
            break
        else:
            i = bets[-1]["id"]
    # TODO: Need a better way to determine equality of bets. `id` is not sufficient
    # At least some bets have duplicate ids.
    # assert len(bets) == len({b.id for b in bets})
    return bets


def get_all_bets(
    username: Optional[str] = None,
    userId: Optional[str] = None,
    marketId: Optional[str] = None,
    marketSlug: Optional[str] = None,
    after: int = 0,
    limit: int = sys.maxsize,
) -> List[Bet]:
    """Get all bets by a specific user.
    Unlike get_bets, this will get all available bets, without a limit
    on the number fetched.
    Automatically calls the bets endpoint until all data has been read.
    You must provide at least one of the arguments, otherwise the server
    will be very sad.

    Args:
        username: The user to get bets for.
        userId: The ID of the user to get bets for.
        marketId: The ID of the market to get bets for.
        marketSlug: The slug of the market to get bets for.
        after: If present, will only fetch bets created after this timestamp.
        limit: The maximum number of bets to retrieve.
        as_json: Whether to return the raw JSON response from the API.
    """
    return [
        weak_structure(x, Bet)
        for x in _get_all_bets(
            username=username,
            userId=userId,
            marketId=marketId,
            marketSlug=marketSlug,
            after=after,
            limit=limit,
        )
    ]


def _get_comments(
    marketId: Optional[str] = None, marketSlug: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Underlying API call for `get_comments`."""
    params = {}
    if marketId is not None:
        params["contractId"] = marketId
    if marketSlug is not None:
        params["contractSlug"] = marketSlug
    resp = requests.get(COMMENTS_URL, params)
    resp.raise_for_status()
    return resp.json()


def get_comments(
    marketId: Optional[str] = None, marketSlug: Optional[str] = None
) -> List[Comment]:
    """Get comments, optionally for a market.

    Args:
        marketId: Id of the market to get comments for.
        marketSlug: Slug of the market to get comments for.
    """
    return [weak_structure(x, Comment) for x in _get_comments(marketId, marketSlug)]


def get_groups() -> List[Group]:
    """Get a list of all groups."""
    resp = requests.get(GROUPS_URL, timeout=20)
    resp.raise_for_status()
    return [weak_structure(x, Group) for x in resp.json()]


def get_group_by_slug(slug: str) -> Group:
    """Get a group by its slug."""
    resp = requests.get(GROUP_SLUG_URL.format(group_slug=slug), timeout=20)
    resp.raise_for_status()
    return weak_structure(resp.json(), Group)


def get_group_by_id(group_id: str) -> Group:
    """Get a group by its ID."""
    resp = requests.get(GROUP_ID_URL.format(group_id=group_id), timeout=20)
    resp.raise_for_status()
    return weak_structure(resp.json(), Group)


def get_group_markets(group_id: str) -> List[Market]:
    """Get all markets attached to a group."""
    resp = requests.get(GROUP_MARKETS_URL.format(group_id=group_id), timeout=20)
    resp.raise_for_status()
    return [weak_structure(x, Market) for x in resp.json()]


def get_market(market_id: str) -> Market:
    """Get a single market.
    Will not include bets or comments.

    Args:
        market_id: ID of the market to get.

    """
    resp = requests.get(SINGLE_MARKET_URL.format(market_id), timeout=20)
    resp.raise_for_status()
    return Market.from_json(resp.json())


def get_market_positions(
    market_id: str,
    order: Optional[OrderType] = None,
    top: Optional[int] = None,
    bottom: Optional[int] = None,
    userId: Optional[str] = None,
) -> List[ContractMetric]:
    """Get the positions on a single market.

    Args:
        market_id: ID of the market to get.
        order: The ordering for results. Can be either "profit" or "shares".
        top: The number of top positions (ordered by order) to return.
        bottom: The number of bottom positions (ordered by order) to return.
        userId: The user ID to query by. Default: null. If provided, only the position for this user will be returned.
    """
    params = {"order": order, "top": top, "bottom": bottom, "userId": userId}
    resp = requests.get(POSITION_URL.format(market_id), timeout=20, params=params)
    resp.raise_for_status()
    return [ContractMetric.from_json(x) for x in resp.json()]


def get_full_market(market_id: str) -> Market:
    """Get a single full market.
    Will include bets and comments

    Args:
        market_id: ID of the market to fetch.
    """
    market = get_market(market_id)
    market.bets = get_bets(marketId=market_id, limit=None)
    market.comments = get_comments(marketId=market_id)
    return market


def _get_markets(
    limit: int = 1000, before: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get a list of markets (not including comments or bets).
    [API reference](https://docs.manifold.markets/api#get-v0markets)


    Args:
        limit: Number of markets to fetch. Max 1000.
        before: ID of a market to fetch markets before.

    Returns:
        The list of markets as raw JSON.
    """
    params: Dict[str, Any] = {"limit": limit}
    if before is not None:
        params["before"] = before
    resp = requests.get(ALL_MARKETS_URL, params=params)
    resp.raise_for_status()
    return resp.json()


def get_markets(limit: int = 1000, before: Optional[str] = None) -> List[Market]:
    """Get a list of markets (not including comments or bets).
    [API reference](https://docs.manifold.markets/api#get-v0markets)

    Args:
        limit: Number of markets to fetch. Max 1000.
        before: ID of a market to fetch markets before.

    """
    json_markets = _get_markets(limit=limit, before=before)
    return [Market.from_json(x) for x in json_markets]


def _get_all_markets(after: int = 0, limit: int = sys.maxsize) -> List[Dict[str, Any]]:
    """Underlying API call for `get_all_markets`.

    Returns:
        Markets as raw JSON.
    """
    markets: List[Dict[str, Any]] = []
    i = None
    while True:
        num_to_get = min(limit - len(markets), 1000)
        if num_to_get <= 0:
            break
        new_markets = [
            x
            for x in _get_markets(limit=num_to_get, before=i)
            if x["createdTime"] > after
        ]
        markets.extend(new_markets)  # type: ignore
        print(f"Fetched {len(markets)} markets.")
        if len(new_markets) < 1000:
            break
        else:
            i = markets[-1]["id"]

    assert len(markets) == len({m["id"] for m in markets})  # type: ignore
    return markets


def get_all_markets(after: int = 0, limit: int = sys.maxsize) -> List[Market]:
    """Get all markets.
    Unlike get_markets, this will get all available markets, without a limit
    on the number fetched.
    Automatically calls the markets endpoint until all data has been read.

    Args:
        after: If present, will only fetch markets created after this timestamp.
        limit: The maximum number of markets to retrieve.
    """
    return [Market.from_json(x) for x in _get_all_markets(after=after, limit=limit)]


def search_markets(terms: List[str]) -> List[Market]:
    """Search markets by terms.
    Returns at most 100 markets.
    Args:
        terms: A list of search terms. Must not contain spaces.
    """
    joined_terms = " ".join(terms)
    params: Dict[str, Any] = {"term": joined_terms}
    resp = requests.get(SEARCH_MARKETS_URL, params=params)
    resp.raise_for_status()
    return [Market.from_json(x) for x in resp.json()]


def get_slug(slug: str) -> Market:
    """Get a market by its slug.
    [API reference](https://docs.manifold.markets/api#get-v0slugmarketslug)
    """
    market = requests.get(MARKET_SLUG_URL.format(slug)).json()
    return Market.from_json(market)


def get_user_by_name(username: str) -> User:
    """Get the data for one user from their username
    [API reference](https://docs.manifold.markets/api#get-v0userusername)

    Args:
        username: The user's username.
    """
    resp = requests.get(USERNAME_URL.format(username))
    resp.raise_for_status()
    return weak_structure(resp.json(), User)


def get_user_by_id(user_id: str) -> User:
    """Get the data for one user from their username
    [API reference](https://docs.manifold.markets/api#get-v0userby-idid)

    Args:
        user_id: The user's ID.
    """
    resp = requests.get(USER_ID_URL.format(user_id))
    resp.raise_for_status()
    return weak_structure(resp.json(), User)


def get_users(limit: int = 1000, before: Optional[str] = None) -> List[User]:
    """Get users up to a limit.
    [API reference](https://docs.manifold.markets/api#get-v0users)

    Args:
        limit: The maximum number of users to get.
        before: The ID of a user to get users before.

    Returns:
        A list of users.
    """
    params: Dict[str, Any] = {"limit": limit}
    if before is not None:
        params["before"] = before
    resp = requests.get(USERS_URL, params=params)  # type: ignore
    resp.raise_for_status()
    return [weak_structure(x, User) for x in resp.json()]


def get_all_users(limit: int = sys.maxsize) -> List[User]:
    """Get a list of all users.
    Repeatedly calls the users endpoint until no new users are returned.

    Args:
        limit: The maximum number of users to get.

    Returns:
        A list of all users.
    """
    users: List[User] = []
    i = None
    while True:
        num_to_get = min(limit - len(users), 1000)
        new_users = get_users(limit=num_to_get, before=i)
        users.extend(new_users)
        if len(new_users) < 1000:
            break
        else:
            i = users[-1].id

    # Users should have unique IDs
    assert len(users) == len({u.id for u in users})
    return users


@define
class APIWrapper:
    key: str

    def __init__(self, key: str) -> None:
        self.key = key

    @property
    def headers(self) -> Dict[str, str]:
        return {"Content-Type": "application/json", "Authorization": f"Key {self.key}"}

    def _prep_add_liquidity(
        self, market_id: str, amount: float
    ) -> requests.PreparedRequest:
        req = requests.Request(
            "POST",
            ADD_LIQUIDITY_URL.format(market_id),
            headers=self.headers,
            json={"amount": amount},
        )
        return req.prepare()

    def add_liquidity(self, market_id: str, amount: float) -> requests.Response:
        """Add liquidity to a market

        Args:
            market_id:  The market to add liquidity to.
            amount:     The amount of liquidity to add.
        """
        prepped = self._prep_add_liquidity(market_id, amount)
        return requests.Session().send(prepped)

    def _prep_me(self) -> requests.PreparedRequest:
        """Prepare a me GET request.
        See `me` for details.
        """
        req = requests.Request("GET", ME_URL, headers=self.headers)
        prepped = req.prepare()
        return prepped

    def me(self) -> requests.Response:
        """Return the authenticated user"""
        prepped = self._prep_me()
        return requests.Session().send(prepped)

    def _prep_make_bet(
        self,
        amount: float,
        contractId: str,
        outcome: str,
        limitProb: Optional[float] = None,
    ) -> requests.PreparedRequest:
        """Prepare a bet POST request.
        See `make_bet` for details.
        """
        data = {"amount": amount, "contractId": contractId, "outcome": outcome}
        if limitProb is not None:
            data["limitProb"] = limitProb
        req = requests.Request("POST", MAKE_BET_URL, headers=self.headers, json=data)
        return req.prepare()

    def make_bet(
        self,
        amount: float,
        contractId: str,
        outcome: str,
        limitProb: Optional[float] = None,
    ) -> requests.Response:
        """Make a bet.
        [API reference](https://docs.manifold.markets/api#post-v0bet)

        Args:
            amount: The amount to bet
            contractId: The market id.
            outcome: The outcome to bet on. YES or NO for binary markets
            limitProb: A limit probability for the bet. If spending the full amount would push the market past this probability, then only enough to push the market to this probability will be bought. Any additional funds will be left often as a bet that can later be matched by an opposing offer.
        """
        prepped = self._prep_make_bet(amount, contractId, outcome, limitProb=limitProb)
        return requests.Session().send(prepped)

    def _prep_cancel_bet(
        self,
        bet_id: str,
    ) -> requests.PreparedRequest:
        """Prepare a cancel bet POST request.
        See `cancel_bet` for details.
        """
        req = requests.Request(
            "POST", CANCEL_BET_URL.format(bet_id), headers=self.headers
        )
        prepped = req.prepare()
        return prepped

    def cancel_bet(
        self,
        bet_id: str,
    ) -> requests.Response:
        """Cancel a bet.
        [API reference](https://docs.manifold.markets/api#post-v0betcancelid)

        Args:
            bet_id: The bet id.
        """
        prepped = self._prep_cancel_bet(bet_id)
        s = requests.Session()
        return s.send(prepped)

    def _prep_create_market(
        self,
        outcomeType: str,
        question: str,
        description: str,
        closeTime: int,
        initialProb: Optional[int] = None,
        min: Optional[float] = None,
        max: Optional[float] = None,
        groupId: Optional[str] = None,
        visibility: Optional[str] = None,
        isLogScale: Optional[bool] = None,
        initialValue: Optional[float] = None,
        answers: Optional[List[str]] = None,
    ) -> requests.PreparedRequest:
        """Prepare a create market POST request
        See `create_market` for details.
        """
        data = {
            "outcomeType": outcomeType,
            "question": question,
            "description": {
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": description,
                            },
                        ],
                    },
                ],
            },
            "closeTime": closeTime,
        }

        if groupId is not None:
            data["groupId"] = groupId

        if visibility is not None:
            data["visibility"] = visibility

        if outcomeType == "BINARY":
            assert initialProb is not None
            assert 1 <= initialProb <= 99
            data["initialProb"] = initialProb
        elif outcomeType == "PSEUDO_NUMERIC":
            assert min is not None
            assert max is not None
            data["min"] = min
            data["max"] = max

            if isLogScale is not None:
                data["isLogScale"] = isLogScale

            if initialValue is not None:
                data["initialValue"] = initialValue
        elif outcomeType == "MULTIPLE_CHOICE":
            assert answers is not None
            data["answers"] = answers

        req = requests.Request(
            "POST", CREATE_MARKET_URL, headers=self.headers, json=data
        )
        return req.prepare()

    def create_market(
        self,
        outcomeType: OutcomeType,
        question: str,
        description: str,
        closeTime: int,
        initialProb: Optional[int] = None,
        min: Optional[float] = None,
        max: Optional[float] = None,
        groupId: Optional[str] = None,
        visibility: Optional[Visibility] = None,
        isLogScale: Optional[bool] = None,
        initialValue: Optional[float] = None,
        answers: Optional[List[str]] = None,
    ) -> requests.Response:
        """Create a new market
        [API reference](https://docs.manifold.markets/api#post-v0market)

        Args:
            outcomeType:    The kind of market.
            question:       Short description of the market.
            description:    Additional details about the market.
            closeTime:      When the market closes (milliseconds since epoch).
            initialProb:    The initial probability for the market. Must be between 1 and 99. Used for BINARY markets.
            min:            Minimum value the market can resolve to. Used for PSEUDO_NUMERIC markets.
            max:            Maximum value the market can resolve to. Used for PSEUDO_NUMERIC markets.
            groupId:        The ID of the group the market belongs to, if any.
            visibility:     The visibility of the market. Must be 'public' or 'unlisted'
            isLogScale:     If True, the scale between min and max uses exponential increments. Used for PSEUDO_NUMERIC markets.
            initialValue:   The initial value of the market. Used for PSEUDO_NUMERIC markets.
            answers:        The possible answers for the market. Used for MULTIPLE_CHOICE markets.
        """
        prepped = self._prep_create_market(
            outcomeType,
            question,
            description,
            closeTime,
            initialProb=initialProb,
            min=min,
            max=max,
            groupId=groupId,
            visibility=visibility,
            isLogScale=isLogScale,
            initialValue=initialValue,
            answers=answers,
        )
        return requests.Session().send(prepped)

    def _prep_resolve(
        self,
        market_id: str,
        outcome: str,
        probabilityInt: Optional[int] = None,
        resolutions: Optional[List[Any]] = None,
        value: Optional[Any] = None,
    ) -> requests.PreparedRequest:
        """Prepare a resolve market POST request
        See `resolve_market` for details
        """
        # At most one of these should be set
        assert (
            (probabilityInt is not None)
            + (resolutions is not None)
            + (value is not None)
        ) <= 1
        data: Dict[str, Any] = {"outcome": outcome}
        if probabilityInt is not None:
            data["probabilityInt"] = probabilityInt
        elif resolutions is not None:
            data["resolutions"] = resolutions
        elif value is not None:
            data["value"] = value

        req = requests.Request(
            "POST",
            RESOLVE_MARKET_URL.format(market_id),
            headers=self.headers,
            json=data,
        )
        return req.prepare()

    def resolve_market(
        self,
        market_id: str,
        outcome: str,
        probabilityInt: Optional[int] = None,
        resolutions: Optional[List[Any]] = None,
        value: Optional[Any] = None,
    ) -> requests.Response:
        """Resolve an existing market.
        [API reference](https://docs.manifold.markets/api#post-v0marketmarketidresolve)

        Args:
            market_id: The id of the market to resolve.
            outcome: The outcome to resolve with.
            probabilityInt: The probability to resolve with (if outcome is MKT)
            resolutions: An array of responses and weights for each response (for resolving free responses with multiple outcomes)
            value: The value the market resolves to (for numeric markets)
        """
        prepped = self._prep_resolve(
            market_id,
            outcome,
            probabilityInt=probabilityInt,
            resolutions=resolutions,
            value=value,
        )
        return requests.Session().send(prepped)

    def _prep_sell(
        self,
        market_id: str,
        outcome: Optional[str] = None,
        shares: Optional[int] = None,
    ) -> requests.PreparedRequest:
        """Prepare a sell POST request.
        See `sell_shares` for details.
        """
        data: Dict[str, Any] = {}
        if outcome is not None:
            data["outcome"] = outcome
        if shares is not None:
            data["shares"] = shares

        req = requests.Request(
            "POST", SELL_SHARES_URL.format(market_id), headers=self.headers, json=data
        )
        return req.prepare()

    def sell_shares(
        self,
        market_id: str,
        outcome: Optional[str] = None,
        shares: Optional[int] = None,
    ) -> requests.Response:
        """Sell shares in a particular market

        Args:
            market_id: The market to sell shares in
            outcome: The kind of shares to sell. Must be YES or NO.
        """
        prepped = self._prep_sell(market_id, outcome, shares=shares)
        return requests.Session().send(prepped)

    def _prep_make_comment(
        self,
        contractId: str,
        content: str,  # The comment to post, formatted as Markdown,
    ) -> requests.PreparedRequest:
        """Prepare a comment POST request.
        See `make_comment` for details.
        """
        data = {"contractId": contractId, "markdown": content}
        req = requests.Request(
            "POST", MAKE_COMMENT_URL, headers=self.headers, json=data
        )
        return req.prepare()

    def make_comment(
        self,
        contractId: str,
        content: str,  # The comment to post, formatted as Markdown,
    ) -> requests.Response:
        """Post a comment.
        [API reference](https://docs.manifold.markets/api#post-v0comment)

        Args:
            contractId: The market id.
            content: The comment to post, formatted as a markdown string.
        """
        prepped = self._prep_make_comment(contractId, content)
        return requests.Session().send(prepped)


def use_api(f):
    """Automatically create an API Wrapper and use it"""

    def wrapped(key: str, *args, **kwargs):
        wrapper = APIWrapper(key)
        return getattr(wrapper, f.__name__)(*args, **kwargs)

    return wrapped


@use_api
def add_liquidity(key: str, market_id: str, amount: float):
    """See `APIWrapper.add_liquidity`."""


@use_api
def cancel_bet(
    key: str,
    bet_id: str,
):
    """See `APIWrapper.cancel_bet`."""


@use_api
def create_market(
    key: str,
    outcomeType: OutcomeType,
    question: str,
    description: str,
    closeTime: int,
    initialProb: Optional[int] = None,
    min: Optional[float] = None,
    max: Optional[float] = None,
    groupId: Optional[str] = None,
    visibility: Optional[Visibility] = None,
    isLogScale: Optional[bool] = None,
    initialValue: Optional[float] = None,
    answers: Optional[List[str]] = None,
):
    """See `APIWrapper.create_market`."""


@use_api
def make_bet(
    key: str,
    amount: float,
    contractId: str,
    outcome: str,
    limitProb: Optional[float] = None,
):
    """See `APIWrapper.make_bet`."""


@use_api
def me(key: str):
    """See `APIWrapper.me`."""


@use_api
def resolve_market(
    key: str,
    market_id: str,
    outcome: str,
    probabilityInt: Optional[int] = None,
    resolutions: Optional[List[Any]] = None,
    value: Optional[Any] = None,
):
    """See `APIWrapper.resolve_market`."""


@use_api
def sell_shares(key: str, market_id: str, outcome: str, shares: Optional[int] = None):
    """See `APIWrapper.sell_shares`."""
