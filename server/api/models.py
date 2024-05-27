from django.db import models

ROLE_CHOICES = (
    (0, "user"),
    (1, "manager"),
    (2, "admin"),
)

TIME_CHOICES = (
    (0, "breakfast"),
    (1, "lunch"),
    (2, "snack"),
    (3, "dinner"),
)


class Model:
    objects = models.Manager()

    @classmethod
    def secure_get(cls, multiple: bool = False, **kwargs):
        if multiple:
            return cls.objects.filter(**kwargs).all()
        return cls.objects.filter(**kwargs).first()


class User(models.Model, Model):
    user_id = models.CharField(primary_key=True, max_length=16)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=60)
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=32)
    weight = models.FloatField(null=True, blank=True)
    body_fat = models.FloatField(null=True, blank=True)
    blood_pressure = models.IntegerField(null=True, blank=True)
    heart_rate = models.IntegerField(null=True, blank=True)
    oxygen_level = models.IntegerField(null=True, blank=True)
    role = models.SmallIntegerField(default=0)  # type: ignore
    date_of_birth = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_seen_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "User"

    @property
    def token(self):
        return f"@{self.user_id}:{self.password}"


class Profile(models.Model, Model):
    profile_id = models.BigAutoField(primary_key=True)
    preferences = models.JSONField(default=dict)
    fk_diet = models.ForeignKey("Diet", on_delete=models.CASCADE, null=True, blank=True)
    fk_nutrition = models.ForeignKey(
        "Nutrition", on_delete=models.SET_NULL, null=True, blank=True
    )
    fk_user = models.ForeignKey("User", on_delete=models.CASCADE)

    class Meta:
        db_table = "Profile"


class Diet(models.Model, Model):
    diet_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=32)
    description = models.TextField(default="", blank=True)
    photo_url = models.TextField()

    class Meta:
        db_table = "Diet"


class MealPlan(models.Model, Model):
    meal_plan_id = models.BigAutoField(primary_key=True)
    time = models.SmallIntegerField(default=0, choices=TIME_CHOICES)  # type: ignore
    fk_diet = models.ForeignKey("Diet", on_delete=models.CASCADE)
    foods = models.TextField()

    class Meta:
        db_table = "MealPlan"

    def get_foods(self) -> list["Food"]:
        diets = [
            Food.secure_get(food_id=int(i)) for i in str(self.foods).split(",") if i
        ]
        return [i for i in diets if i]


class Submission(models.Model, Model):
    submission_id = models.BigAutoField(primary_key=True)
    note = models.TextField()
    reviewer = models.CharField(max_length=16, null=True, blank=True)
    fk_user = models.ForeignKey("User", on_delete=models.CASCADE)
    is_accepted = models.BooleanField(default=False)  # type: ignore

    class Meta:
        db_table = "Submission"


class Food(models.Model, Model):
    food_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=32)
    description = models.TextField()
    photo_url = models.TextField()
    carbs = models.FloatField()
    protein = models.FloatField()
    fat = models.FloatField()
    calories = models.FloatField()
    fk_nutrition = models.ForeignKey("Nutrition", on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = "Food"


class Nutrition(models.Model, Model):
    nutrition_id = models.BigAutoField(primary_key=True)
    vitamins = models.JSONField(default=dict)
    minerals = models.JSONField(default=dict)
    amino_acids = models.JSONField(default=dict)

    class Meta:
        db_table = "Nutrition"
