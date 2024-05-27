from typing import Union

import tablib
from rest_framework.serializers import ModelSerializer

from .admin import *
from .models import Diet, Food, MealPlan, Nutrition, Profile, Submission
from .serializers import *
from .utils import *


def get_user(user_id: str, lang) -> tuple[int, Union[dict, User]]:
    query_user: User = User.secure_get(user_id=user_id)

    if not query_user:
        return 404, {"error": lang.translate("user.not_found", user_id)}

    return 200, query_user


def get_all(
    query_id: str, results: list, serializer: type[ModelSerializer], lang: Lang
):
    parts = query_id.split(":")
    if len(parts) != 2 and [True for part in parts if not part.isnumeric()]:
        return 409, {
            "error": "Invalid format, must be: `[page]:[size]`",
        }
    page, size = int(parts[0]), int(parts[1])
    return 200, {
        "overflow": max(0, len(results) - (page * size) - size),
        "results": [
            serializer(lang, food).data for food in results[page : page + size]
        ],
    }


class AccountView(View):
    class Register(Args):
        user_id: str = ValidString(16)  # type: ignore
        password: str = ValidPassword()  # type: ignore
        email: str = ValidEmail()  # type: ignore
        first_name: str = ValidString(32)  # type: ignore
        last_name: str = ValidString(32)  # type: ignore
        date_of_birth: str = ValidDate()  # type: ignore

    def post_register(self, post: Register):
        if User.secure_get(user_id=post.user_id) or User.secure_get(email=post.email):
            return 409, {
                "error": self.lang.translate("user.already_exists", post.user_id)
            }

        user = User(**post.as_dict(filters=["password", "date_of_birth"]))
        user.date_of_birth = datetime.datetime(*[int(i) for i in post.date_of_birth.split("-")])  # type: ignore
        user.password = str(Password.encrypt(post.password), encoding="utf-8")  # type: ignore
        user.save()

        return 200, {"token": user.token}

    class Login(Args):
        user_id: str = ValidString(16)  # type: ignore
        password: str = ValidPassword()  # type: ignore

    def post_login(self, post: Login):
        user: User = User.secure_get(user_id=post.user_id)
        if not user:
            return 404, {"error": self.lang.translate("user.not_found", post.user_id)}

        if not Password.compare(str(user.password), post.password):
            return 409, {"error": self.lang.translate("user.wrong_password")}

        return 200, {"token": user.token}

    def delete_delete(self, user: User, query_id: str):
        if not user.role == 2:
            return 403, {"error": self.lang.translate("user.no_permission")}

        code, query = get_user(query_id, self.lang)
        if code != 200:
            return code, query

        cast(User, query).delete()
        return 200, {}

    def get_query(self, query_id: str):
        code, query = get_user(query_id, self.lang)
        if code != 200:
            return code, query

        return 200, UserSerializer(self.lang, query).data

    def get_all(self, query_id: str):
        return get_all(query_id, User.objects.all(), UserSerializer, self.lang)

    class Edit(Args):
        user_id: str = ValidString(16)  # type: ignore
        password: str = ValidPassword(is_optional=True)  # type: ignore
        email: str = ValidEmail(is_optional=True)  # type: ignore
        first_name: str = ValidString(32, is_optional=True)  # type: ignore
        last_name: str = ValidString(32, is_optional=True)  # type: ignore
        date_of_birth: str = ValidDate(is_optional=True)  # type: ignore
        role: int = ValidInteger(is_optional=True)  # type: ignore

    def post_edit(self, post: Edit, user: User):
        query_user: User = User.secure_get(user_id=post.user_id)
        if not query_user:
            return 404, {"error": self.lang.translate("user.not_found", post.user_id)}

        if user.user_id != query_user.user_id and user.role != 2:
            return 403, {"error": self.lang.translate("user.no_permission")}

        if post.email:
            query_user.email = post.email  # type: ignore
        if post.first_name:
            query_user.first_name = post.first_name  # type: ignore
        if post.last_name:
            query_user.last_name = post.last_name  # type: ignore
        if post.date_of_birth:
            query_user.date_of_birth = datetime.datetime(*[int(i) for i in reversed(post.date_of_birth.split("/"))])  # type: ignore
        if post.password:
            query_user.password = str(Password.encrypt(post.password), encoding="utf-8")  # type: ignore
        if post.role is not None and user.role == 2 and post.role in [0, 1, 2]:
            query_user.role = post.role  # type: ignore
        query_user.save()

        return 200, UserSerializer(self.lang, query_user).data

    def get_profile(self, query_id: str):
        code, query = get_user(query_id, self.lang)
        if code != 200:
            return code, query

        profile = Profile.secure_get(fk_user=query)
        if profile is None:
            profile = Profile(fk_user=query)
            profile.save()

        return 200, ProfileSerializer(self.lang, profile).data


class FoodView(View):
    class Create(Args):
        name: str = ValidString(32)  # type: ignore
        description: str = ValidString()  # type: ignore
        photo_url: str = ValidUrl()  # type: ignore
        carbs: str = ValidFloat()  # type: ignore
        protein: str = ValidFloat()  # type: ignore
        fat: str = ValidFloat()  # type: ignore
        calories: str = ValidFloat()  # type: ignore
        vitamins: str = ValidJson({i: ValidFloat() for i in VITAMINS})  # type: ignore
        minerals: str = ValidJson({i: ValidFloat() for i in MINERALS})  # type: ignore
        amino_acids: str = ValidJson({i: ValidFloat() for i in AMINO_ACIDS})  # type: ignore

    def post_create(self, post: Create, user: User):
        if user.role == 0:
            return 403, {"error": self.lang.translate("user.no_permission")}

        food = Food(**post.as_dict(filters=["vitamins", "minerals", "amino_acids"]))
        nutrition = Nutrition(
            vitamins=json.dumps(post.vitamins),
            minerals=json.dumps(post.minerals),
            amino_acids=json.dumps(post.amino_acids),
        )
        nutrition.save()

        food.fk_nutrition = nutrition  # type: ignore
        food.save()
        return 200, FoodSerializer(self.lang, food).data

    def get_query(self, query_id: int):
        food = Food.secure_get(food_id=query_id)

        if food is None:
            return 404, {"error": self.lang.translate("generic.not_found", query_id)}

        return 200, FoodSerializer(self.lang, food).data

    def get_all(self, query_id: str):
        return get_all(query_id, Food.objects.all(), FoodSerializer, self.lang)

    def delete_delete(self, user: User, query_id: int):
        if user.role == 0:
            return 403, {"error": self.lang.translate("user.no_permission")}

        food: Food = Food.secure_get(food_id=query_id)

        if food is None:
            return 404, {"error": self.lang.translate("generic.not_found", query_id)}

        food.fk_nutrition.delete()  # type: ignore
        food.delete()

        return 200, {}

    class Edit(Args):
        food_id: str = ValidInteger()  # type: ignore
        name: str = ValidString(32, is_optional=True)  # type: ignore
        description: str = ValidString(is_optional=True)  # type: ignore
        photo_url: str = ValidUrl(is_optional=True)  # type: ignore
        carbs: str = ValidFloat(is_optional=True)  # type: ignore
        protein: str = ValidFloat(is_optional=True)  # type: ignore
        fat: str = ValidFloat(is_optional=True)  # type: ignore
        calories: str = ValidFloat(is_optional=True)  # type: ignore
        vitamins: str = ValidJson({i: ValidFloat() for i in VITAMINS}, is_optional=True)  # type: ignore
        minerals: str = ValidJson({i: ValidFloat() for i in MINERALS}, is_optional=True)  # type: ignore
        amino_acids: str = ValidJson({i: ValidFloat() for i in AMINO_ACIDS}, is_optional=True)  # type: ignore

    def post_edit(self, post: Edit, user: User):
        if user.role == 0:
            return 403, {"error": self.lang.translate("user.no_permission")}

        food: Food = Food.secure_get(food_id=post.food_id)
        if food is None:
            return 404, {
                "error": self.lang.translate("generic.not_found", post.food_id)
            }

        if post.name:
            food.name = post.name  # type: ignore
        if post.description:
            food.description = post.description  # type: ignore
        if post.photo_url:
            food.photo_url = post.photo_url  # type: ignore
        if post.carbs:
            food.carbs = post.carbs  # type: ignore
        if post.protein:
            food.protein = post.protein  # type: ignore
        if post.fat:
            food.fat = post.fat  # type: ignore
        if post.calories:
            food.calories = post.calories  # type: ignore
        if post.vitamins:
            food.fk_nutrition.vitamins = json.dumps(post.vitamins)  # type: ignore
        if post.minerals:
            food.fk_nutrition.minerals = json.dumps(post.minerals)  # type: ignore
        if post.amino_acids:
            food.fk_nutrition.amino_acids = json.dumps(post.amino_acids)  # type: ignore

        return 200, FoodSerializer(self.lang, food).data


class SubmissionView(View):
    class Create(Args):
        note: str = ValidString()  # type: ignore

    def post_create(self, post: Create, user: User):
        submission = Submission(note=post.note, fk_user=user)
        submission.save()

        return 200, SubmissionSerializer(self.lang, submission).data

    def get_query(self, query_id: str):
        submission = Submission.secure_get(submission_id=query_id)

        if submission is None:
            return 404, {"error": self.lang.translate("generic.not_found", query_id)}

        return 200, SubmissionSerializer(self.lang, submission).data

    def get_all(self, query_id: str):
        return get_all(
            query_id, Submission.objects.all(), SubmissionSerializer, self.lang
        )

    def delete_delete(self, user: User, query_id: str):
        submission: Submission = Submission.secure_get(submission_id=query_id)
        if user.role == 0 and submission.fk_user.user_id != user.user_id:  # type: ignore
            return 403, {"error": self.lang.translate("user.no_permission")}

        if submission is None:
            return 404, {"error": self.lang.translate("generic.not_found", query_id)}

        submission.delete()

        return 200, {}

    class Edit(Args):
        submission_id: str = ValidInteger()  # type: ignore
        note: str = ValidString(is_optional=True)  # type: ignore
        is_accepted: str = ValidBoolean(is_optional=True)  # type: ignore

    def post_edit(self, post: Edit, user: User):
        submission: Submission = Submission.secure_get(submission_id=post.submission_id)
        if user.role == 0 and submission.fk_user.user_id != user.user_id:  # type: ignore
            return 403, {"error": self.lang.translate("user.no_permission")}

        if submission is None:
            return 404, {
                "error": self.lang.translate("generic.not_found", post.submission_id)
            }

        if post.note:
            submission.note = post.note  # type: ignore
        if post.is_accepted:
            if post.is_accepted:
                submission.reviewer = user.user_id
            if not post.is_accepted:
                submission.reviewer = None  # type: ignore
            submission.is_accepted = post.is_accepted  # type: ignore
        submission.save()

        return 200, SubmissionSerializer(self.lang, submission).data


class DietView(View):
    class Create(Args):
        name: str = ValidString(32)  # type: ignore
        description: str = ValidString(is_optional=True)  # type: ignore
        photo_url: str = ValidUrl()  # type: ignore

    def post_create(self, post: Create, user: User):
        if user.role == 0:  # type: ignore
            return 403, {"error": self.lang.translate("user.no_permission")}

        diet = Diet(**post.as_dict())
        diet.save()

        return 200, DietSerializer(self.lang, diet).data

    def get_query(self, query_id: str):
        diet = Diet.secure_get(diet_id=query_id)

        if diet is None:
            return 404, {"error": self.lang.translate("generic.not_found", query_id)}

        return 200, DietSerializer(self.lang, diet).data

    def get_all(self, query_id: str):
        return get_all(query_id, Diet.objects.all(), DietSerializer, self.lang)

    class Edit(Args):
        diet_id: str = ValidInteger()  # type: ignore
        name: str = ValidString(32, is_optional=True)  # type: ignore
        description: str = ValidString(is_optional=True)  # type: ignore
        photo_url: str = ValidUrl(is_optional=True)  # type: ignore

    def post_edit(self, post: Edit, user: User):
        if user.role == 0:  # type: ignore
            return 403, {"error": self.lang.translate("user.no_permission")}

        diet: Diet = Diet.secure_get(diet_id=post.diet_id)

        if diet is None:
            return 404, {
                "error": self.lang.translate("generic.not_found", post.diet_id)
            }

        if post.name:
            diet.name = post.name  # type: ignore
        if post.description:
            diet.description = post.description  # type: ignore
        if post.photo_url:
            diet.photo_url = post.photo_url  # type: ignore

        diet.save()

        return 200, DietSerializer(self.lang, diet).data

    def delete_delete(self, user: User, query_id: str):
        if user.role == 0:  # type: ignore
            return 403, {"error": self.lang.translate("user.no_permission")}

        diet: Diet = Diet.secure_get(diet_id=query_id)

        if diet is None:
            return 404, {"error": self.lang.translate("generic.not_found", query_id)}

        diet.delete()

        return 200, {}


class MealPlanView(View):
    class Create(Args):
        time: str = ValidMealTime()  # type: ignore
        diet_id: str = ValidInteger()  # type: ignore
        foods: str = ValidList()  # type: ignore

    def post_create(self, post: Create, user: User):
        if user.role == 0:  # type: ignore
            return 403, {"error": self.lang.translate("user.no_permission")}

        diet = Diet.secure_get(diet_id=post.diet_id)

        if diet is None:
            return 404, {
                "error": self.lang.translate("generic.not_found", post.diet_id)
            }

        meal_plan = MealPlan(
            time=post.time, fk_diet=diet, foods=",".join([str(i) for i in post.foods])
        )
        meal_plan.save()

        return 200, MealPlanSerializer(self.lang, meal_plan).data

    def get_query(self, query_id: str):
        meal_plan = MealPlan.secure_get(meal_plan_id=query_id)

        if meal_plan is None:
            return 404, {"error": self.lang.translate("generic.not_found", query_id)}

        return 200, MealPlanSerializer(self.lang, meal_plan).data

    def get_all(self, query_id: str):
        return get_all(query_id, MealPlan.objects.all(), MealPlanSerializer, self.lang)

    def delete_delete(self, query_id: str):
        meal_plan = MealPlan.secure_get(meal_plan_id=query_id)

        if meal_plan is None:
            return 404, {"error": self.lang.translate("generic.not_found", query_id)}

        meal_plan.delete()

        return 200, {}


class SystemView(View):
    def get_backup(self, user: User, query_id: str):
        if user.role != 2:
            return 403, {"error": self.lang.translate("user.no_permission")}

        match query_id:
            case "users":
                return 201, UserResource().export(format="csv").csv  # type: ignore
            case "profiles":
                return 201, ProfileResource().export(format="csv").csv  # type: ignore
            case "diets":
                return 201, DietResource().export(format="csv").csv  # type: ignore
            case "meal_plans":
                return 201, MealPlanResource().export(format="csv").csv  # type: ignore
            case "submissions":
                return 201, SubmissionResource().export(format="csv").csv  # type: ignore
            case "foods":
                return 201, FoodResource().export(format="csv").csv  # type: ignore
            case "nutritions":
                return 201, NutritionResource().export(format="csv").csv  # type: ignore
            case _:
                return 201, ""

    class Rollback(Args):
        resource: str = ValidString()  # type: ignore
        data: str = ValidString()  # type: ignore

    def post_rollback(self, post: Rollback, user: User):
        if user.role != 2:
            return 403, {"error": self.lang.translate("user.no_permission")}

        data = tablib.Dataset()
        data.csv = post.data  # type: ignore

        match post.resource:
            case "users":
                return 200, {
                    "has_errors": UserResource().import_data(data).has_errors()  # type: ignore
                }
            case "profiles":
                return 200, {
                    "has_errors": ProfileResource().import_data(data).has_errors()  # type: ignore
                }
            case "diets":
                return 200, {
                    "has_errors": DietResource().import_data(data).has_errors()  # type: ignore
                }
            case "meal_plans":
                return 200, {
                    "has_errors": MealPlanResource().import_data(data).has_errors()  # type: ignore
                }
            case "submissions":
                return 200, {
                    "has_errors": SubmissionResource().import_data(data).has_errors()  # type: ignore
                }
            case "foods":
                return 200, {
                    "has_errors": FoodResource().import_data(data).has_errors()  # type: ignore
                }
            case "nutritions":
                return 200, {
                    "has_errors": NutritionResource().import_data(data).has_errors()  # type: ignore
                }
            case _:
                return 201, ""


class IotView(View):
    class Update(Args):
        user_id: str = ValidString(16)  # type: ignore
        blood_pressure: int = ValidInteger()  # type: ignore
        heart_rate: int = ValidInteger()  # type: ignore
        oxygen_level: int = ValidInteger()  # type: ignore

    def post_update(self, post: Update):
        query_user: User = User.secure_get(user_id=post.user_id)
        if query_user is None:
            return 404, {"error": self.lang.translate("user.not_found", post.user_id)}

        query_user.heart_rate = post.heart_rate  # type: ignore
        query_user.oxygen_level = post.oxygen_level  # type: ignore
        query_user.blood_pressure = post.blood_pressure  # type: ignore
        query_user.save()

        return 200, UserSerializer(self.lang, query_user).data
