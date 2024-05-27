from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import Diet, Food, MealPlan, Nutrition, Profile, Submission, User


class UserResource(resources.ModelResource):
    class Meta:
        model = User
        import_id_fields = ("user_id",)


class DietResource(resources.ModelResource):
    class Meta:
        model = Diet
        import_id_fields = ("diet_id",)


class FoodResource(resources.ModelResource):
    class Meta:
        model = Food
        import_id_fields = ("food_id",)


class ProfileResource(resources.ModelResource):
    class Meta:
        model = Profile
        import_id_fields = ("profile_id",)


class MealPlanResource(resources.ModelResource):
    class Meta:
        model = MealPlan
        import_id_fields = ("meal_plan_id",)


class NutritionResource(resources.ModelResource):
    class Meta:
        model = Nutrition
        import_id_fields = ("nutrition_id",)


class SubmissionResource(resources.ModelResource):
    class Meta:
        model = Submission
        import_id_fields = ("submission_id",)


class Admin(ImportExportModelAdmin):
    resource_classes = [
        UserResource,
        ProfileResource,
        DietResource,
        MealPlanResource,
        SubmissionResource,
        FoodResource,
        NutritionResource,
    ]


admin.site.register(User, Admin)
admin.site.register(Diet, Admin)
admin.site.register(Food, Admin)
admin.site.register(Profile, Admin)
admin.site.register(MealPlan, Admin)
admin.site.register(Nutrition, Admin)
admin.site.register(Submission, Admin)
