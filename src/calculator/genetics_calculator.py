"""
Processes form data from heredity_calculator_new.html and returns
child phenotype probabilities for every supported trait.

Traits handled:
  1.  eye_color — Колір очей        (polygenic simplified to 2-gene model)
  2.  hair_color — Колір волосся     (multi-allele dominant hierarchy)
  3.  hair_type — Тип волосся       (incomplete dominance: curly/wavy/straight)
  4.  blood — Група крові       (ABO codominance)
  5.  rh — Резус-фактор      (simple dominant)
  6.  height — Ріст              (polygenic simplified to 2-gene model)
  7.  dimples — Ямочки            (simple dominant)
  8.  freckles — Веснянки          (simple dominant)
"""

from __future__ import annotations
from fractions import Fraction
from itertools import product
from typing import Optional


def _normalize_pair(a: str, b: str) -> tuple[str, str]:
    """Return (dominant_first, recessive_second) pair, sorted consistently."""
    if a == b:
        return (a, b)
    if a.isupper() and b.islower():
        return (a, b)
    if b.isupper() and a.islower():
        return (b, a)
    return tuple(sorted([a, b], reverse=True))


def _punnett(f_a1: str, f_a2: str, m_a1: str, m_a2: str) -> dict[tuple, Fraction]:
    """Return {(a1,a2): probability} for all 4 Punnett combinations."""
    combos: dict[tuple, Fraction] = {}
    for ga, gb in product([f_a1, f_a2], [m_a1, m_a2]):
        key = _normalize_pair(ga, gb)
        combos[key] = combos.get(key, Fraction(0)) + Fraction(1, 4)
    return combos


def _phenotype_of_simple(a1: str, a2: str, dominant_ph: str, recessive_ph: str) -> str:
    """Simple dominance: any dominant allele → dominant phenotype."""
    if a1.isupper() or a2.isupper():
        return dominant_ph
    return recessive_ph


UNKNOWN = "unknown"
MISSING  = ""


def _is_known(val: Optional[str]) -> bool:
    return bool(val) and val not in (UNKNOWN, MISSING)


class SimpleTrait:
    """
    Single-locus, simple-dominance trait.

    dominant_allele  – e.g. 'D'   (uppercase)
    recessive_allele – e.g. 'd'   (lowercase)
    dominant_ph – human-readable dominant phenotype value from HTML
    recessive_ph – human-readable recessive phenotype value from HTML
    """

    def __init__(
        self,
        name: str,
        dominant_allele: str,
        dominant_ph: str,
        recessive_ph: str,
    ):
        self.name = name
        self.D = dominant_allele.upper()
        self.r = dominant_allele.lower()
        self.dominant_ph = dominant_ph
        self.recessive_ph = recessive_ph

    def genotypes_for(self, phenotype: str) -> list[tuple[str, str]]:
        """Return list of (a1, a2) genotype tuples consistent with phenotype."""
        if phenotype == self.recessive_ph:
            return [(self.r, self.r)]
        return [(self.D, self.D), (self.D, self.r)]

    def phenotype_of(self, a1: str, a2: str) -> str:
        return _phenotype_of_simple(a1, a2, self.dominant_ph, self.recessive_ph)

    def parent_genotype_dist(
        self,
        parent_ph: Optional[str],
        gp1_ph: Optional[str],
        gp2_ph: Optional[str],
    ) -> dict[tuple[str, str], Fraction]:
        """
        Returns probability distribution over parent genotypes.

        Priority:
          1. If both grandparents known → Punnett-infer, then filter by parent_ph
          2. If only parent_ph known → uniform prior over consistent genotypes
          3. If nothing known → uniform prior over all 3 genotypes
        """
        if _is_known(gp1_ph) and _is_known(gp2_ph):
            dist = self._from_grandparents(gp1_ph, gp2_ph)
        elif _is_known(parent_ph):
            genos = self.genotypes_for(parent_ph)
            dist = {g: Fraction(1, len(genos)) for g in genos}
        else:
            all_g = [(self.D, self.D), (self.D, self.r), (self.r, self.r)]
            dist = {g: Fraction(1, 3) for g in all_g}

        if _is_known(parent_ph):
            filtered = {
                g: p for g, p in dist.items()
                if self.phenotype_of(*g) == parent_ph
            }
            total = sum(filtered.values())
            if total > 0:
                dist = {g: p / total for g, p in filtered.items()}

        return dist

    def _from_grandparents(self, gp1_ph: str, gp2_ph: str) -> dict[tuple, Fraction]:
        """Compute parent genotype distribution via grandparent Punnett squares."""
        gp1_genos = self.genotypes_for(gp1_ph)
        gp2_genos = self.genotypes_for(gp2_ph)
        dist: dict[tuple, Fraction] = {}
        combo_n = len(gp1_genos) * len(gp2_genos)
        for g1, g2 in product(gp1_genos, gp2_genos):
            weight = Fraction(1, combo_n)
            for (ca, cb), prob in _punnett(g1[0], g1[1], g2[0], g2[1]).items():
                key = _normalize_pair(ca, cb)
                dist[key] = dist.get(key, Fraction(0)) + weight * prob
        return dist

    def child_probabilities(
        self,
        father_dist: dict[tuple, Fraction],
        mother_dist: dict[tuple, Fraction],
    ) -> dict[str, float]:
        """Cross two parent genotype distributions → child phenotype probabilities."""
        child: dict[str, Fraction] = {}
        for (fg, fp), (mg, mp) in product(father_dist.items(), mother_dist.items()):
            weight = fp * mp
            for (ca, cb), prob in _punnett(fg[0], fg[1], mg[0], mg[1]).items():
                ph = self.phenotype_of(ca, cb)
                child[ph] = child.get(ph, Fraction(0)) + weight * prob
        return {ph: float(p) for ph, p in child.items()}

    def calculate(
        self,
        father_ph: Optional[str],
        mother_ph: Optional[str],
        father_gp1_ph: Optional[str],
        father_gp2_ph: Optional[str],
        mother_gp1_ph: Optional[str],
        mother_gp2_ph: Optional[str],
        ) -> dict[str, float]:
        f_dist = self.parent_genotype_dist(father_ph, father_gp1_ph, father_gp2_ph)
        m_dist = self.parent_genotype_dist(mother_ph, mother_gp1_ph, mother_gp2_ph)
        return self.child_probabilities(f_dist, m_dist)


class HairTypeTrait:
    """
    Incomplete dominance:
      CC → curly
      Cs → wavy
      ss → straight
    """
    CURLY = "curly"
    WAVY = "wavy"
    STRAIGHT = "straight"

    PHENOTYPE_TO_GENOTYPES = {
        CURLY: [("C", "C")],
        WAVY: [("C", "s")],
        STRAIGHT: [("s", "s")],
    }

    def phenotype_of(self, a1: str, a2: str) -> str:
        pair = frozenset([a1, a2])
        if pair == {"C"}:
            return self.CURLY
        if pair == {"s"}:
            return self.STRAIGHT
        return self.WAVY

    def genotypes_for(self, ph: str) -> list[tuple[str, str]]:
        return self.PHENOTYPE_TO_GENOTYPES.get(ph, [("C", "C"), ("C", "s"), ("s", "s")])

    def parent_genotype_dist(
        self,
        parent_ph: Optional[str],
        gp1_ph: Optional[str],
        gp2_ph: Optional[str],
    ) -> dict[tuple, Fraction]:
        if _is_known(gp1_ph) and _is_known(gp2_ph):
            gp1_genos = self.genotypes_for(gp1_ph)
            gp2_genos = self.genotypes_for(gp2_ph)
            dist: dict[tuple, Fraction] = {}
            n = len(gp1_genos) * len(gp2_genos)
            for g1, g2 in product(gp1_genos, gp2_genos):
                w = Fraction(1, n)
                for (ca, cb), prob in _punnett(g1[0], g1[1], g2[0], g2[1]).items():
                    k = tuple(sorted([ca, cb], reverse=True))
                    dist[k] = dist.get(k, Fraction(0)) + w * prob
        elif _is_known(parent_ph):
            genos = self.genotypes_for(parent_ph)
            dist = {g: Fraction(1, len(genos)) for g in genos}
        else:
            all_g = [("C", "C"), ("C", "s"), ("s", "s")]
            dist = {g: Fraction(1, 3) for g in all_g}

        if _is_known(parent_ph):
            filtered = {g: p for g, p in dist.items() if self.phenotype_of(*g) == parent_ph}
            total = sum(filtered.values())
            if total > 0:
                dist = {g: p / total for g, p in filtered.items()}

        return dist

    def calculate(
        self,
        father_ph: Optional[str],
        mother_ph: Optional[str],
        father_gp1_ph: Optional[str],
        father_gp2_ph: Optional[str],
        mother_gp1_ph: Optional[str],
        mother_gp2_ph: Optional[str],
    ) -> dict[str, float]:
        f_dist = self.parent_genotype_dist(father_ph, father_gp1_ph, father_gp2_ph)
        m_dist = self.parent_genotype_dist(mother_ph, mother_gp1_ph, mother_gp2_ph)

        child: dict[str, Fraction] = {}
        for (fg, fp), (mg, mp) in product(f_dist.items(), m_dist.items()):
            weight = fp * mp
            for (ca, cb), prob in _punnett(fg[0], fg[1], mg[0], mg[1]).items():
                ph = self.phenotype_of(ca, cb)
                child[ph] = child.get(ph, Fraction(0)) + weight * prob
        return {ph: float(p) for ph, p in child.items()}


class BloodTypeTrait:
    """
    ABO: IA and IB are codominant; both dominate i.
    Phenotype values match the HTML: 'O', 'A', 'B', 'AB'
    """

    PHENOTYPE_TO_GENOTYPES: dict[str, list[tuple[str, str]]] = {
        "O":  [("i", "i")],
        "A":  [("IA", "IA"), ("IA", "i")],
        "B":  [("IB", "IB"), ("IB", "i")],
        "AB": [("IA", "IB")],
    }

    @staticmethod
    def _ph(a1: str, a2: str) -> str:
        pair = frozenset([a1, a2])
        if pair == frozenset(["IA", "IB"]):
            return "AB"
        if "IA" in pair:
            return "A"
        if "IB" in pair:
            return "B"
        return "O"

    @staticmethod
    def _punnett_abo(g1: tuple, g2: tuple) -> dict[tuple, Fraction]:
        combos: dict[tuple, Fraction] = {}
        for a, b in product(g1, g2):
            key = tuple(sorted([a, b], reverse=True))
            combos[key] = combos.get(key, Fraction(0)) + Fraction(1, 4)
        return combos

    def genotypes_for(self, ph: str) -> list[tuple]:
        return self.PHENOTYPE_TO_GENOTYPES.get(ph, [])

    def parent_genotype_dist(
        self,
        parent_ph: Optional[str],
        gp1_ph: Optional[str],
        gp2_ph: Optional[str],
    ) -> dict[tuple, Fraction]:
        if _is_known(gp1_ph) and _is_known(gp2_ph):
            gp1_genos = self.genotypes_for(gp1_ph)
            gp2_genos = self.genotypes_for(gp2_ph)
            dist: dict[tuple, Fraction] = {}
            n = len(gp1_genos) * len(gp2_genos)
            for g1, g2 in product(gp1_genos, gp2_genos):
                w = Fraction(1, n)
                for (ca, cb), prob in self._punnett_abo(g1, g2).items():
                    k = tuple(sorted([ca, cb], reverse=True))
                    dist[k] = dist.get(k, Fraction(0)) + w * prob
        elif _is_known(parent_ph):
            genos = self.genotypes_for(parent_ph)
            dist = {g: Fraction(1, len(genos)) for g in genos}
        else:
            # uniform over all 6 genotypes
            all_g = [("IA","IA"),("IA","IB"),("IA","i"),("IB","IB"),("IB","i"),("i","i")]
            dist = {g: Fraction(1, 6) for g in all_g}

        if _is_known(parent_ph):
            filtered = {g: p for g, p in dist.items() if self._ph(*g) == parent_ph}
            total = sum(filtered.values())
            if total > 0:
                dist = {g: p / total for g, p in filtered.items()}

        return dist

    def calculate(
        self,
        father_ph: Optional[str],
        mother_ph: Optional[str],
        father_gp1_ph: Optional[str],
        father_gp2_ph: Optional[str],
        mother_gp1_ph: Optional[str],
        mother_gp2_ph: Optional[str],
    ) -> dict[str, float]:
        f_dist = self.parent_genotype_dist(father_ph, father_gp1_ph, father_gp2_ph)
        m_dist = self.parent_genotype_dist(mother_ph, mother_gp1_ph, mother_gp2_ph)

        child: dict[str, Fraction] = {}
        for (fg, fp), (mg, mp) in product(f_dist.items(), m_dist.items()):
            weight = fp * mp
            for (ca, cb), prob in self._punnett_abo(fg, mg).items():
                ph = self._ph(ca, cb)
                child[ph] = child.get(ph, Fraction(0)) + weight * prob
        return {ph: float(p) for ph, p in child.items()}


class EyeColorTrait:
    """
    2-gene model for eye color.
    Gene B: B (brown dominant) / b
    Gene G: G (green dominant) / g — only expressed when bb
    """

    HTML_TO_CATEGORY = {
        "brown": "brown",
        "hazel": "brown",
        "green": "green",
        "blue": "blue",
        "gray": "blue",
    }
    PHENOTYPES = ["brown", "green", "blue"]

    def genotypes_for(self, ph: str) -> list[tuple]:
        if ph == "brown":
            return [
                ("B","B","G","G"), ("B","B","G","g"), ("B","B","g","g"),
                ("B","b","G","G"), ("B","b","G","g"), ("B","b","g","g"),
            ]
        if ph == "green":
            return [("b","b","G","G"), ("b","b","G","g")]
        return [("b","b","g","g")]

    @staticmethod
    def _phenotype_of(B1, B2, G1, G2) -> str:
        if "B" in (B1, B2):
            return "brown"
        if "G" in (G1, G2):
            return "green"
        return "blue"

    def _punnett_2gene(self, fg: tuple, mg: tuple) -> dict[tuple, Fraction]:
        """4-allele Punnett for 2-gene model."""
        combos: dict[tuple, Fraction] = {}
        for (fB, fG), (mB, mG) in product(
            [(fg[0], fg[2]), (fg[0], fg[3]), (fg[1], fg[2]), (fg[1], fg[3])],
            [(mg[0], mg[2]), (mg[0], mg[3]), (mg[1], mg[2]), (mg[1], mg[3])],
        ):
            child_B = tuple(sorted([fB, mB], reverse=True))
            child_G = tuple(sorted([fG, mG], reverse=True))
            key = child_B + child_G 
            combos[key] = combos.get(key, Fraction(0)) + Fraction(1, 16)
        return combos

    def parent_genotype_dist(
        self,
        parent_ph: Optional[str],
        gp1_ph: Optional[str],
        gp2_ph: Optional[str],
    ) -> dict[tuple, Fraction]:
        cat_parent = self.HTML_TO_CATEGORY.get(parent_ph) if _is_known(parent_ph) else None
        cat_gp1    = self.HTML_TO_CATEGORY.get(gp1_ph) if _is_known(gp1_ph) else None
        cat_gp2    = self.HTML_TO_CATEGORY.get(gp2_ph) if _is_known(gp2_ph) else None

        if cat_gp1 and cat_gp2:
            gp1_genos = self.genotypes_for(cat_gp1)
            gp2_genos = self.genotypes_for(cat_gp2)
            dist: dict[tuple, Fraction] = {}
            n = len(gp1_genos) * len(gp2_genos)
            for g1, g2 in product(gp1_genos, gp2_genos):
                w = Fraction(1, n)
                for key, prob in self._punnett_2gene(g1, g2).items():
                    dist[key] = dist.get(key, Fraction(0)) + w * prob
        elif cat_parent:
            genos = self.genotypes_for(cat_parent)
            dist = {g: Fraction(1, len(genos)) for g in genos}
        else:
            all_g = self.genotypes_for("brown") + self.genotypes_for("green") + self.genotypes_for("blue")
            dist = {g: Fraction(1, len(all_g)) for g in all_g}

        if cat_parent:
            filtered = {
                g: p for g, p in dist.items()
                if self._phenotype_of(*g) == cat_parent
            }
            total = sum(filtered.values())
            if total > 0:
                dist = {g: p / total for g, p in filtered.items()}

        return dist

    def calculate(
        self,
        father_ph: Optional[str],
        mother_ph: Optional[str],
        father_gp1_ph: Optional[str],
        father_gp2_ph: Optional[str],
        mother_gp1_ph: Optional[str],
        mother_gp2_ph: Optional[str],
    ) -> dict[str, float]:
        f_dist = self.parent_genotype_dist(father_ph, father_gp1_ph, father_gp2_ph)
        m_dist = self.parent_genotype_dist(mother_ph, mother_gp1_ph, mother_gp2_ph)

        child: dict[str, Fraction] = {}
        for (fg, fp), (mg, mp) in product(f_dist.items(), m_dist.items()):
            weight = fp * mp
            for key, prob in self._punnett_2gene(fg, mg).items():
                ph = self._phenotype_of(*key)
                child[ph] = child.get(ph, Fraction(0)) + weight * prob
        return {ph: float(p) for ph, p in child.items()}


class HairColorTrait:
    """2-gene simplified model for hair color."""

    HTML_TO_CATEGORY = {
        "black": "dark",
        "dark_brown": "dark",
        "brown": "dark",
        "red": "red",
        "blonde": "blonde",
    }

    def genotypes_for(self, ph: str) -> list[tuple]:
        if ph == "dark":
            return [
                ("D","D","R","R"), ("D","D","R","r"), ("D","D","r","r"),
                ("D","d","R","R"), ("D","d","R","r"), ("D","d","r","r"),
            ]
        if ph == "red":
            return [("d","d","R","R"), ("d","d","R","r")]
        return [("d","d","r","r")]

    @staticmethod
    def _phenotype_of(D1, D2, R1, R2) -> str:
        if "D" in (D1, D2):
            return "dark"
        if "R" in (R1, R2):
            return "red"
        return "blonde"

    def _punnett_2gene(self, fg: tuple, mg: tuple) -> dict[tuple, Fraction]:
        combos: dict[tuple, Fraction] = {}
        for (fD, fR), (mD, mR) in product(
            [(fg[0], fg[2]), (fg[0], fg[3]), (fg[1], fg[2]), (fg[1], fg[3])],
            [(mg[0], mg[2]), (mg[0], mg[3]), (mg[1], mg[2]), (mg[1], mg[3])],
        ):
            cD = tuple(sorted([fD, mD], reverse=True))
            cR = tuple(sorted([fR, mR], reverse=True))
            key = cD + cR
            combos[key] = combos.get(key, Fraction(0)) + Fraction(1, 16)
        return combos

    def parent_genotype_dist(
        self,
        parent_ph: Optional[str],
        gp1_ph: Optional[str],
        gp2_ph: Optional[str],
    ) -> dict[tuple, Fraction]:
        cat_p  = self.HTML_TO_CATEGORY.get(parent_ph) if _is_known(parent_ph) else None
        cat_g1 = self.HTML_TO_CATEGORY.get(gp1_ph) if _is_known(gp1_ph) else None
        cat_g2 = self.HTML_TO_CATEGORY.get(gp2_ph) if _is_known(gp2_ph) else None

        if cat_g1 and cat_g2:
            gp1_genos = self.genotypes_for(cat_g1)
            gp2_genos = self.genotypes_for(cat_g2)
            dist: dict[tuple, Fraction] = {}
            n = len(gp1_genos) * len(gp2_genos)
            for g1, g2 in product(gp1_genos, gp2_genos):
                w = Fraction(1, n)
                for key, prob in self._punnett_2gene(g1, g2).items():
                    dist[key] = dist.get(key, Fraction(0)) + w * prob
        elif cat_p:
            genos = self.genotypes_for(cat_p)
            dist = {g: Fraction(1, len(genos)) for g in genos}
        else:
            all_g = (self.genotypes_for("dark") + self.genotypes_for("red")
                     + self.genotypes_for("blonde"))
            dist = {g: Fraction(1, len(all_g)) for g in all_g}

        if cat_p:
            filtered = {g: p for g, p in dist.items() if self._phenotype_of(*g) == cat_p}
            total = sum(filtered.values())
            if total > 0:
                dist = {g: p / total for g, p in filtered.items()}

        return dist

    def calculate(
        self,
        father_ph: Optional[str],
        mother_ph: Optional[str],
        father_gp1_ph: Optional[str],
        father_gp2_ph: Optional[str],
        mother_gp1_ph: Optional[str],
        mother_gp2_ph: Optional[str],
    ) -> dict[str, float]:
        f_dist = self.parent_genotype_dist(father_ph, father_gp1_ph, father_gp2_ph)
        m_dist = self.parent_genotype_dist(mother_ph, mother_gp1_ph, mother_gp2_ph)

        child: dict[str, Fraction] = {}
        for (fg, fp), (mg, mp) in product(f_dist.items(), m_dist.items()):
            weight = fp * mp
            for key, prob in self._punnett_2gene(fg, mg).items():
                ph = self._phenotype_of(*key)
                child[ph] = child.get(ph, Fraction(0)) + weight * prob
        return {ph: float(p) for ph, p in child.items()}


class HeightTrait:
    """
    2-gene additive model for height.
    Alleles: A/a and B/b (each uppercase = +1 height unit)
    Score → phenotype:
      3–4 → tall
      2 → medium
      0–1 → short
    """
    HTML_TO_CATEGORY = {
        "tall": "tall",
        "medium": "medium",
        "short": "short",
    }

    ALL_GENOS = [
        ("A","A","B","B"), ("A","A","B","b"), ("A","A","b","b"),
        ("A","a","B","B"), ("A","a","B","b"), ("A","a","b","b"),
        ("a","a","B","B"), ("a","a","B","b"), ("a","a","b","b"),
    ]

    @staticmethod
    def _score(A1, A2, B1, B2) -> int:
        return sum(1 for a in [A1, A2, B1, B2] if a.isupper())

    def _phenotype_of(self, A1, A2, B1, B2) -> str:
        s = self._score(A1, A2, B1, B2)
        if s >= 3:
            return "tall"
        if s == 2:
            return "medium"
        return "short"

    def genotypes_for(self, ph: str) -> list[tuple]:
        return [g for g in self.ALL_GENOS if self._phenotype_of(*g) == ph]

    def _punnett_2gene(self, fg: tuple, mg: tuple) -> dict[tuple, Fraction]:
        combos: dict[tuple, Fraction] = {}
        for (fA, fB), (mA, mB) in product(
            [(fg[0], fg[2]), (fg[0], fg[3]), (fg[1], fg[2]), (fg[1], fg[3])],
            [(mg[0], mg[2]), (mg[0], mg[3]), (mg[1], mg[2]), (mg[1], mg[3])],
        ):
            cA = tuple(sorted([fA, mA], reverse=True))
            cB = tuple(sorted([fB, mB], reverse=True))
            key = cA + cB
            combos[key] = combos.get(key, Fraction(0)) + Fraction(1, 16)
        return combos

    def parent_genotype_dist(
        self,
        parent_ph: Optional[str],
        gp1_ph: Optional[str],
        gp2_ph: Optional[str],
    ) -> dict[tuple, Fraction]:
        cat_p  = self.HTML_TO_CATEGORY.get(parent_ph) if _is_known(parent_ph) else None
        cat_g1 = self.HTML_TO_CATEGORY.get(gp1_ph) if _is_known(gp1_ph) else None
        cat_g2 = self.HTML_TO_CATEGORY.get(gp2_ph) if _is_known(gp2_ph) else None

        if cat_g1 and cat_g2:
            gp1_genos = self.genotypes_for(cat_g1)
            gp2_genos = self.genotypes_for(cat_g2)
            dist: dict[tuple, Fraction] = {}
            n = len(gp1_genos) * len(gp2_genos)
            for g1, g2 in product(gp1_genos, gp2_genos):
                w = Fraction(1, n)
                for key, prob in self._punnett_2gene(g1, g2).items():
                    dist[key] = dist.get(key, Fraction(0)) + w * prob
        elif cat_p:
            genos = self.genotypes_for(cat_p)
            dist = {g: Fraction(1, len(genos)) for g in genos}
        else:
            dist = {g: Fraction(1, len(self.ALL_GENOS)) for g in self.ALL_GENOS}

        if cat_p:
            filtered = {g: p for g, p in dist.items() if self._phenotype_of(*g) == cat_p}
            total = sum(filtered.values())
            if total > 0:
                dist = {g: p / total for g, p in filtered.items()}

        return dist

    def calculate(
        self,
        father_ph: Optional[str],
        mother_ph: Optional[str],
        father_gp1_ph: Optional[str],
        father_gp2_ph: Optional[str],
        mother_gp1_ph: Optional[str],
        mother_gp2_ph: Optional[str],
    ) -> dict[str, float]:
        f_dist = self.parent_genotype_dist(father_ph, father_gp1_ph, father_gp2_ph)
        m_dist = self.parent_genotype_dist(mother_ph, mother_gp1_ph, mother_gp2_ph)

        child: dict[str, Fraction] = {}
        for (fg, fp), (mg, mp) in product(f_dist.items(), m_dist.items()):
            weight = fp * mp
            for key, prob in self._punnett_2gene(fg, mg).items():
                ph = self._phenotype_of(*key)
                child[ph] = child.get(ph, Fraction(0)) + weight * prob
        return {ph: float(p) for ph, p in child.items()}


_EYE_COLOR   = EyeColorTrait()
_HAIR_COLOR  = HairColorTrait()
_HAIR_TYPE   = HairTypeTrait()
_BLOOD_TYPE  = BloodTypeTrait()
_RH_FACTOR   = SimpleTrait("Rh Factor", "R", dominant_ph="pos", recessive_ph="neg")
_DIMPLES     = SimpleTrait("Dimples", "D", dominant_ph="yes", recessive_ph="no")
_FRECKLES    = SimpleTrait("Freckles", "F", dominant_ph="yes", recessive_ph="no")
_HEIGHT      = HeightTrait()


class GeneticCalculator:
    """
    Accepts a dict of form fields and returns a dict of child phenotype probability 
    distributions per trait. Returns an empty dict for traits with no parent info.
    """

    def _get(self, data: dict, key: str) -> Optional[str]:
        """Return value or None if missing/unknown/empty."""
        v = data.get(key, "")
        # Assuming _is_known is defined elsewhere in your file
        return v if _is_known(v) else None

    def calculate(self, form_data: dict) -> dict[str, dict[str, float]]:
        d = form_data
        g = self._get

        # Define mapping of trait keys to their respective calculation objects 
        # and their specific form field suffixes
        trait_mapping = {
            "eye_color": (_EYE_COLOR, "eye"),
            "hair_color": (_HAIR_COLOR, "hair_color"),
            "hair_type": (_HAIR_TYPE, "hair_type"),
            "blood": (_BLOOD_TYPE, "blood"),
            "rh": (_RH_FACTOR, "rh"),
            "height": (_HEIGHT, "height"),
            "dimples": (_DIMPLES, "dimples"),
            "freckles": (_FRECKLES, "freckles"),
        }

        results: dict[str, dict[str, float]] = {}

        for trait_key, (calculator_obj, form_suffix) in trait_mapping.items():
            # Extract primary parent info
            f_ph = g(d, f"father_{form_suffix}")
            m_ph = g(d, f"mother_{form_suffix}")

            # If NO parent info is provided, return empty dict for this trait
            if f_ph is None and m_ph is None:
                results[trait_key] = {}
                continue

            # Otherwise, perform full calculation with grandparents
            results[trait_key] = calculator_obj.calculate(
                father_ph = f_ph,
                mother_ph = m_ph,
                father_gp1_ph = g(d, f"pf_father_{form_suffix}"),
                father_gp2_ph = g(d, f"pf_mother_{form_suffix}"),
                mother_gp1_ph = g(d, f"pm_father_{form_suffix}"),
                mother_gp2_ph = g(d, f"pm_mother_{form_suffix}"),
            )

        return results
