import random

SUITS = ["black", "orange", "green", "red"]

VALUES = [*range(5, 15), 1]

CARDS = ["bird"] + [f" {s[0]}{v}" for s in SUITS for v in VALUES]

PLAYERS = ["alf", "bess", "cate", "duke"]


def card_suit(c):
    smap = {s[0]: s for s in SUITS}
    return smap[c[1]]


def card_points(c):
    if c == "bird":
        return 20
    v = int(c[2:])
    return {1: 15, 14: 10, 10: 10, 5: 5}.get(v, 0)


class Hand:
    def __init__(self, cards):
        self.orig_cards = cards
        self.cards = cards[:]

    def __repr__(self):
        suits = [[c for c in self.cards if c.startswith(f" {s[0]}")] for s in SUITS]
        suits.sort(key=len, reverse=True)

        p = [
            [c for c in self.cards if c == "bird"],
            *[list(self.order_desc(Game(), s, inc_bird=False)) for s in suits],
        ]

        p2 = sum(p, [])

        return "".join([f"{c:5}" for c in p2])

    def max_bid(self, g):
        b = any([c == "bird" for c in self.cards])
        suits = [[c for c in self.cards if c.startswith(f" {s[0]}")] for s in SUITS]
        suits.sort(key=len, reverse=True)

        return min(
            180,
            100
            + (len(suits[0]) + (1 if b else 0)) * 5
            - (max(len(suits[2]) + len(suits[3]) - 3, 0) * 5),
        )

    def suit_value(self, g, cards):
        values = {
            1: 4,
            14: 3.1,
            13: 3,
            12: 2.2,
            11: 2,
            10: 1.8,
            9: 1.4,
            8: 1.3,
            7: 1.2,
            6: 1.1,
            5: 1.0,
        }

        return sum([values[int(c[2:])] for c in cards])

    def order_desc(self, g, cards, inc_bird):
        if len(cards):
            for c in g.iter_suit_desc(card_suit(cards[0]), inc_bird=inc_bird):
                if c in cards:
                    yield c

    def swap_kitty(self, g, kitty):
        cards = [*self.cards, *kitty.cards]

        b = [c for c in cards if c == "bird"]
        suits = [[c for c in cards if c.startswith(f" {s[0]}")] for s in SUITS]
        suits.sort(key=lambda c_arr: self.suit_value(g, c_arr), reverse=True)

        trump_cards = list(self.order_desc(g, suits[0] + b, inc_bird=True))
        suits234 = [
            list(self.order_desc(g, cards, inc_bird=False))
            for cards in suits[1:]
            if len(cards)
        ]

        # retain high cards from 2nd, 3rd & 4th suits
        retain = []
        for ocards in suits234:
            for oc, dc in zip(
                ocards, g.iter_suit_desc(card_suit(ocards[0]), inc_bird=False)
            ):
                if oc == dc:
                    retain.append(oc)
                else:
                    break

        priority = trump_cards[:]
        priority += retain

        for ocards in suits234:
            for c in ocards:
                if c not in priority:
                    priority.append(c)

        self.cards = priority[:10]
        self.discards = priority[10:]

        # recompute from the saved 10
        b = [c for c in self.cards if c == "bird"]
        suits = [[c for c in self.cards if c.startswith(f" {s[0]}")] for s in SUITS]
        suits.sort(key=lambda c_arr: self.suit_value(g, c_arr), reverse=True)
        trump_cards = suits[0] + b
        suits234 = [cards for cards in suits[1:] if len(cards)]

        partner = None

        # pick partner from high trump
        toptier = 3 if len(trump_cards) >= 6 else 5
        for tc, dc in zip(
            trump_cards[:toptier],
            g.iter_suit_desc(card_suit(trump_cards[0]), inc_bird=True),
        ):
            if tc != dc:
                partner = dc
                break

        # or, pick partner from high off color
        if not partner:
            for ocards in suits234:
                for oc, dc in zip(
                    ocards[:3],
                    g.iter_suit_desc(card_suit(ocards[0]), inc_bird=False),
                ):
                    if oc != dc:
                        partner = dc
                        break

        if not partner:
            # seems like you have it pretty well covered
            partner = random.choice(trump_cards + retain)

        g.declare(trump=card_suit(suits[0][0]), partner=partner)

    def play(self, g, t):
        smap = g.suit_sorted(self.cards)

        if len(t.cards) == 0:
            # I have the lead
            c = random.choice(self.cards)
        elif t.suit_led(g) in smap:
            # follow the lead
            c = random.choice(smap[t.suit_led(g)])
        else:
            # play something else
            c = random.choice(self.cards)

        self.cards.remove(c)
        t.play(c)


class Kitty:
    def __init__(self, cards):
        self.cards = cards

    def __repr__(self):
        return "".join([f"{c:5}" for c in self.cards])


class Trick:
    def __init__(self):
        self.cards = []
        self.players = []

    @property
    def played(self):
        return [c[1] for c in self.cards]

    def played_by(self, card):
        for p, c in self.cards:
            if c == card:
                return p

    def __repr__(self):
        return "".join([f"{c:5}" for c in self.played])

    def suit_led(self, g):
        c = self.cards[0][1]
        if c == "bird":
            return g.trump
        return card_suit(c)

    def play(self, c):
        self.cards.append([self.players[-1], c])


class Game:
    ROOK_MODE = "10.5"  # "low", "high", "wild"
    PARTNER = "pick"
    GAME_TRICKS = 10

    def iter_suit_desc(self, suit, inc_bird):
        for v in reversed(VALUES):
            if inc_bird and v == 1 and self.ROOK_MODE == "high":
                yield "bird"
            if inc_bird and v == 10 and self.ROOK_MODE == "10.5":
                yield "bird"
            yield f" {suit[0]}{v}"
            if inc_bird and v == 5 and self.ROOK_MODE == "low":
                yield "bird"

    def declare(self, trump, partner=None):
        assert partner if self.PARTNER == "pick" else True

        self.trump = trump
        self.partner = partner

        print(f"Trump: {trump}; partner: {partner}")

    def deal(self):
        cards = CARDS[:]
        random.shuffle(cards)

        return {
            "hands": [
                Hand(cards[0:10]),
                Hand(cards[10:20]),
                Hand(cards[20:30]),
                Hand(cards[30:40]),
            ],
            "kitty": Kitty(cards[40:]),
        }

    def suit_sorted(self, cards):
        b = [c for c in cards if c == "bird"]
        suits = [[c for c in cards if c.startswith(f" {s[0]}")] for s in SUITS]

        suits = [scards for scards in suits if scards]

        smap = {card_suit(suitlist[0]): suitlist for suitlist in suits}
        if len(b):
            smap[self.trump] = smap.get(self.trump, []) + b

        return smap

    def order_desc(self, cards, inc_bird):
        if len(cards) == 1 and cards[0] == "bird":
            if inc_bird:
                yield cards[0]
        elif len(cards):
            suits = [card_suit(c) for c in cards if c != "bird"]
            assert len(set(suits)) == 1

            for c in self.iter_suit_desc(list(suits)[0], inc_bird=inc_bird):
                if c in cards:
                    yield c

    def points(self, cards):
        return sum(card_points(c) for c in cards)

    def takes(self, t):
        smap = self.suit_sorted([c[1] for c in t.cards])
        if self.trump in smap:
            candidates = self.order_desc(smap[self.trump], True)
        else:
            candidates = self.order_desc(smap[t.suit_led(self)], False)
        c = list(candidates)[0]
        for player, card in t.cards:
            if card == c:
                return player


def main():
    g = Game()

    dealt = g.deal()

    hands = dealt["hands"]

    win_bid = None
    b = 0
    for index, h in enumerate(hands):
        mbid = h.max_bid(g)
        if mbid > b:
            b = mbid
            takes = index
            win_bid = mbid
        print(f"{PLAYERS[index]:6}: ", h, h.max_bid(g))

    print("kitty :", dealt["kitty"])
    print()

    print(f"kitty by {PLAYERS[takes]} ({win_bid} winning bid)")
    hands[takes].swap_kitty(g, dealt["kitty"])

    for index, h in enumerate(hands):
        print(f"{PLAYERS[index]:6}: ", h)

    # play out the tricks
    lead = takes
    tricks = []
    for i in range(g.GAME_TRICKS):
        t = Trick()

        print(f"\n{PLAYERS[lead]} leads; trick {i+1}")

        for index in [(lead + i) % 4 for i in range(4)]:
            t.players.append(index)
            h = hands[index]
            h.play(g, t)

        print(t)
        lead = g.takes(t)
        print(f" --> {PLAYERS[lead]} takes trick: {g.points(t.played)} points")
        tricks.append(t)

    print()

    scores = [0 for _ in range(4)]

    partner = None
    for trick in tricks:
        if g.partner in trick.played:
            partner = trick.played_by(g.partner)
        scores[g.takes(trick)] += g.points(trick.played)
    last_hand_take = g.takes(tricks[-1])
    print(
        f" --> {PLAYERS[last_hand_take]} takes final trick: {g.points(hands[takes].discards)} discarded"
    )
    scores[last_hand_take] += g.points(hands[takes].discards)

    for index, score in enumerate(scores):
        print(f"{PLAYERS[index]:6}: {score}")

    print()
    opposition = [index for index in range(4) if index not in [takes, partner]]
    if partner == takes:
        print(
            f"{PLAYERS[takes]:6}(solo) : {scores[takes]} {'WON' if scores[takes] > win_bid else 'LOST'}"
        )
    else:
        leader = scores[takes] + scores[partner]
        print(
            f"{PLAYERS[takes]+' '+PLAYERS[partner]:12} : {leader} {'WON' if leader > win_bid else 'LOST'}"
        )
    print(
        f"{' '.join([PLAYERS[i] for i in opposition]):12} : {sum([scores[i] for i in opposition])}"
    )


if __name__ == "__main__":
    main()
