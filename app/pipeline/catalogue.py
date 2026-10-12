"""Built-in Indian meal catalogue for the offline planner.

Calories and protein are approximate home-cooking values (about 1 tsp oil per
dish) and should be reviewed by a nutritionist before launch.
"""

from dataclasses import dataclass

SLOTS = ("breakfast", "mid_morning", "lunch", "evening_snack", "dinner")


@dataclass(frozen=True)
class Meal:
    slot: str
    name: str
    portion: str
    kcal: int
    protein_g: int
    kind: str  # vegan | veg | egg | nonveg
    cuisine: str  # north | south | west | east | any
    jain: bool  # can be cooked without onion, garlic and root vegetables
    tags: frozenset[str]
    ingredients: tuple[tuple[str, float, str, str], ...]  # name, quantity, unit, category


def _meal(slot, name, portion, kcal, protein, kind, cuisine, jain, ingredients, tags="") -> Meal:
    parsed = []
    for item in ingredients.split(";"):
        item_name, quantity, unit, category = (part.strip() for part in item.split(":"))
        parsed.append((item_name, float(quantity), unit, category))
    return Meal(slot, name, portion, kcal, protein, kind, cuisine, jain, frozenset(tags.split()), tuple(parsed))


B, M, L, E, D = SLOTS

MEALS = [
    # --- Breakfast ---------------------------------------------------------------
    _meal(B, "Moong dal chilla with mint chutney and curd", "2 chillas + 1 small bowl curd", 380, 22, "veg", "north", True,
          "moong dal:80:g:pulses; curd:100:g:dairy; mint and coriander:15:g:vegetables"),
    _meal(B, "Vegetable poha with peanuts and buttermilk", "1.5 cups poha + 1 glass chaas", 360, 11, "veg", "west", False,
          "poha:60:g:grains; peanuts:15:g:nuts_seeds; onion:40:g:vegetables; green peas:30:g:vegetables; curd:100:g:dairy", "high_gi"),
    _meal(B, "Idli with sambar", "3 idlis + 1 bowl sambar", 330, 12, "vegan", "south", False,
          "idli batter:180:g:grains; toor dal:30:g:pulses; mixed sambar vegetables:100:g:vegetables"),
    _meal(B, "Vegetable oats upma with curd", "1.5 cups upma + 1 small bowl curd", 350, 14, "veg", "any", False,
          "rolled oats:50:g:grains; mixed vegetables:100:g:vegetables; curd:100:g:dairy"),
    _meal(B, "Besan chilla stuffed with paneer", "2 chillas", 400, 24, "veg", "north", True,
          "besan:60:g:pulses; paneer:60:g:dairy; tomato:50:g:vegetables; capsicum:40:g:vegetables"),
    _meal(B, "Ragi dosa with sambar and coconut chutney", "2 dosas + 1 bowl sambar", 360, 11, "vegan", "south", False,
          "ragi flour:60:g:grains; toor dal:30:g:pulses; mixed sambar vegetables:100:g:vegetables; fresh coconut:20:g:nuts_seeds"),
    _meal(B, "Masala omelette with multigrain toast", "2-egg omelette + 2 slices toast", 380, 22, "egg", "any", False,
          "eggs:2:pieces:protein; multigrain bread:2:slices:grains; onion:30:g:vegetables; tomato:50:g:vegetables"),
    _meal(B, "Sprouted moong salad with a fruit", "1 large bowl sprouts + 1 fruit", 300, 16, "vegan", "any", False,
          "moong sprouts:120:g:pulses; cucumber:80:g:vegetables; tomato:50:g:vegetables; seasonal fruit:1:pieces:fruits; lemon:0.5:pieces:vegetables", "high_iron"),
    _meal(B, "Methi thepla with curd", "2 theplas + 1 small bowl curd", 370, 12, "veg", "west", True,
          "whole wheat flour:60:g:grains; fresh methi:50:g:vegetables; curd:150:g:dairy", "high_iron"),
    _meal(B, "Tofu bhurji with jowar roti", "1 bowl bhurji + 1 roti", 350, 22, "vegan", "any", True,
          "tofu:120:g:protein; jowar flour:35:g:grains; tomato:60:g:vegetables; capsicum:40:g:vegetables"),
    # --- Mid-morning -------------------------------------------------------------
    _meal(M, "Guava or apple with almonds", "1 fruit + 5 almonds", 150, 3, "vegan", "any", True,
          "seasonal fruit:1:pieces:fruits; almonds:6:g:nuts_seeds"),
    _meal(M, "Buttermilk with roasted chana", "1 glass chaas + 1 handful chana", 160, 9, "veg", "any", True,
          "curd:100:g:dairy; roasted chana:30:g:pulses"),
    _meal(M, "Coconut water with peanuts", "1 glass + 1 small handful", 170, 6, "vegan", "any", True,
          "tender coconut:1:pieces:fruits; peanuts:20:g:nuts_seeds"),
    _meal(M, "Papaya bowl with pumpkin seeds", "1 bowl papaya + 1 tbsp seeds", 140, 5, "vegan", "any", True,
          "papaya:200:g:fruits; pumpkin seeds:12:g:nuts_seeds"),
    _meal(M, "Boiled eggs", "1 whole egg + 2 egg whites", 130, 13, "egg", "any", False,
          "eggs:3:pieces:protein"),
    # --- Lunch -------------------------------------------------------------------
    _meal(L, "Phulka, dal tadka, lauki sabzi, salad and curd", "2 phulkas + 1 bowl each", 520, 22, "veg", "north", True,
          "whole wheat flour:60:g:grains; toor dal:40:g:pulses; lauki:150:g:vegetables; salad vegetables:100:g:vegetables; curd:100:g:dairy"),
    _meal(L, "Brown rice with rajma, cucumber raita and salad", "1 cup rice + 1 bowl rajma", 540, 21, "veg", "north", True,
          "brown rice:60:g:grains; rajma:50:g:pulses; curd:100:g:dairy; cucumber:100:g:vegetables; tomato:60:g:vegetables", "high_iron"),
    _meal(L, "Jowar bhakri with pitla, salad and chaas", "2 bhakris + 1 bowl pitla", 500, 20, "veg", "west", True,
          "jowar flour:70:g:grains; besan:40:g:pulses; salad vegetables:100:g:vegetables; curd:100:g:dairy"),
    _meal(L, "Brown rice, sambar, beans poriyal and curd", "1 cup rice + 1 bowl each", 510, 17, "veg", "south", False,
          "brown rice:60:g:grains; toor dal:35:g:pulses; french beans:120:g:vegetables; mixed sambar vegetables:100:g:vegetables; curd:100:g:dairy"),
    _meal(L, "Phulka with palak paneer and salad", "2 phulkas + 1 bowl palak paneer", 530, 26, "veg", "north", True,
          "whole wheat flour:60:g:grains; spinach:200:g:vegetables; paneer:80:g:dairy; salad vegetables:100:g:vegetables", "high_iron"),
    _meal(L, "Phulka with home-style chicken curry and salad", "2 phulkas + 1 bowl curry", 540, 36, "nonveg", "any", False,
          "whole wheat flour:60:g:grains; chicken breast:120:g:protein; onion:50:g:vegetables; tomato:80:g:vegetables; salad vegetables:100:g:vegetables"),
    _meal(L, "Rice with fish curry and sauteed greens", "1 cup rice + 1 bowl curry", 520, 32, "nonveg", "east", False,
          "brown rice:60:g:grains; fish:120:g:protein; spinach:150:g:vegetables; tomato:60:g:vegetables"),
    _meal(L, "Moong dal khichdi with kadhi and salad", "1.5 cups khichdi + 1 bowl kadhi", 500, 19, "veg", "west", True,
          "rice:40:g:grains; moong dal:40:g:pulses; curd:150:g:dairy; besan:15:g:pulses; salad vegetables:100:g:vegetables"),
    _meal(L, "Phulka with chole, salad and chaas", "2 phulkas + 1 bowl chole", 540, 21, "veg", "north", True,
          "whole wheat flour:60:g:grains; kabuli chana:50:g:pulses; tomato:80:g:vegetables; salad vegetables:100:g:vegetables; curd:100:g:dairy", "high_iron"),
    _meal(L, "Foxtail millet pulao with soya chunks and raita", "1.5 cups pulao + 1 bowl raita", 510, 27, "veg", "any", True,
          "foxtail millet:60:g:grains; soya chunks:30:g:protein; mixed vegetables:120:g:vegetables; curd:100:g:dairy"),
    _meal(L, "Phulka with tofu-matar curry and salad", "2 phulkas + 1 bowl curry", 500, 25, "vegan", "any", True,
          "whole wheat flour:60:g:grains; tofu:120:g:protein; green peas:60:g:vegetables; tomato:80:g:vegetables; salad vegetables:100:g:vegetables"),
    # --- Evening snack -----------------------------------------------------------
    _meal(E, "Roasted makhana with green tea", "1 bowl makhana", 130, 4, "vegan", "any", True,
          "makhana:30:g:nuts_seeds; green tea:1:bags:pantry"),
    _meal(E, "Roasted chana with a fruit", "1 handful chana + 1 fruit", 170, 8, "vegan", "any", True,
          "roasted chana:30:g:pulses; seasonal fruit:1:pieces:fruits"),
    _meal(E, "Sprouts chaat", "1 bowl", 150, 9, "vegan", "any", False,
          "moong sprouts:80:g:pulses; tomato:40:g:vegetables; cucumber:50:g:vegetables; lemon:0.5:pieces:vegetables", "high_iron"),
    _meal(E, "Paneer tikka", "6 cubes", 180, 12, "veg", "north", True,
          "paneer:60:g:dairy; capsicum:50:g:vegetables; curd:20:g:dairy"),
    _meal(E, "Masala buttermilk with khakhra", "1 glass chaas + 2 khakhras", 160, 6, "veg", "west", True,
          "curd:100:g:dairy; whole wheat khakhra:2:pieces:grains"),
    _meal(E, "Boiled peanut chaat", "1 small bowl", 170, 8, "vegan", "any", True,
          "peanuts:30:g:nuts_seeds; tomato:40:g:vegetables; lemon:0.5:pieces:vegetables"),
    # --- Dinner ------------------------------------------------------------------
    _meal(D, "Phulka with mixed vegetable sabzi, moong dal and salad", "2 phulkas + 1 bowl each", 430, 18, "vegan", "north", True,
          "whole wheat flour:60:g:grains; moong dal:40:g:pulses; mixed vegetables:150:g:vegetables; salad vegetables:100:g:vegetables"),
    _meal(D, "Vegetable dalia khichdi with curd", "1.5 cups + 1 small bowl curd", 400, 15, "veg", "any", True,
          "dalia:50:g:grains; moong dal:25:g:pulses; mixed vegetables:120:g:vegetables; curd:100:g:dairy"),
    _meal(D, "Grilled paneer with sauteed vegetables and phulka", "100 g paneer + 1 phulka", 440, 28, "veg", "any", True,
          "paneer:100:g:dairy; mixed vegetables:200:g:vegetables; whole wheat flour:30:g:grains", "high_sat_fat"),
    _meal(D, "Grilled chicken with sauteed vegetables and phulka", "120 g chicken + 1 phulka", 420, 38, "nonveg", "any", False,
          "chicken breast:120:g:protein; mixed vegetables:200:g:vegetables; whole wheat flour:30:g:grains"),
    _meal(D, "Egg curry with phulka and salad", "2 eggs + 2 phulkas", 450, 22, "egg", "any", False,
          "eggs:2:pieces:protein; whole wheat flour:60:g:grains; onion:50:g:vegetables; tomato:80:g:vegetables; salad vegetables:100:g:vegetables"),
    _meal(D, "Ragi roti with dal palak and salad", "2 rotis + 1 bowl dal palak", 420, 18, "vegan", "any", True,
          "ragi flour:60:g:grains; moong dal:40:g:pulses; spinach:150:g:vegetables; salad vegetables:100:g:vegetables", "high_iron"),
    _meal(D, "Moong dal soup with tofu stir-fry and phulka", "1 bowl soup + 1 bowl stir-fry + 1 phulka", 400, 26, "vegan", "any", True,
          "moong dal:30:g:pulses; tofu:120:g:protein; mixed vegetables:150:g:vegetables; whole wheat flour:30:g:grains"),
    _meal(D, "Bajra roti with lauki-chana dal and kachumber", "2 rotis + 1 bowl dal", 430, 17, "vegan", "west", True,
          "bajra flour:60:g:grains; chana dal:40:g:pulses; lauki:150:g:vegetables; salad vegetables:100:g:vegetables", "high_iron"),
    _meal(D, "Fish tikka with sauteed vegetables and phulka", "120 g fish + 1 phulka", 410, 34, "nonveg", "any", False,
          "fish:120:g:protein; mixed vegetables:200:g:vegetables; whole wheat flour:30:g:grains; curd:30:g:dairy"),
    _meal(D, "Curd rice with vegetable stir-fry and sundal", "1 cup curd rice + 1 bowl each", 420, 16, "veg", "south", False,
          "rice:50:g:grains; curd:150:g:dairy; mixed vegetables:150:g:vegetables; kabuli chana:30:g:pulses", "high_gi"),
]

# Which meal kinds each diet type may eat.
DIET_KINDS = {
    "vegan": {"vegan"},
    "jain": {"vegan", "veg"},
    "veg": {"vegan", "veg"},
    "eggetarian": {"vegan", "veg", "egg"},
    "non_veg": {"vegan", "veg", "egg", "nonveg"},
}
