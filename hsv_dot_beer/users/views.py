from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from beers.models import UserFavoriteBeer
from beers.serializers import UserFavoriteBeerSerializer
from .models import User
from .permissions import UserPermission
from .serializers import CreateUserSerializer, UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    Updates and retrieves user accounts
    """

    @action(detail=True, methods=["POST"])
    def subscribetobeer(self, request, pk):
        user = get_object_or_404(self.get_queryset(), id=pk)
        body = request.data.copy()
        body["user"] = user.id
        print(body)
        serializer = UserFavoriteBeerSerializer(
            data=body,
            context={"request": request},
        )
        try:
            # validate it as if it's a new subscription
            serializer.is_valid(raise_exception=True)
        except ValidationError as exc:
            print("womp", exc)
            if "beer" in request.data and "notifications_enabled" in request.data:
                # is the user trying to update the existing subscription?
                try:
                    fav = UserFavoriteBeer.objects.get(
                        user=user, beer=request.data["beer"]
                    )
                except UserFavoriteBeer.DoesNotExist:
                    # nope, doesn't exist; raise the error
                    raise exc
                # we do have a favorite instance
                serializer = UserFavoriteBeerSerializer(
                    instance=fav,
                    data=body,
                    context={"request", request},
                )
                if not serializer.is_valid():
                    # nope, still not valid
                    raise exc
                serializer.save()
                return Response(serializer.data)
            # serializer is missing required fields
            raise exc
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=["POST"])
    def unsubscribefrombeer(self, request, pk):
        user = get_object_or_404(self.get_queryset(), id=pk)
        if "beer" not in request.data:
            raise ValidationError({"beer": ["This field is required."]})
        instance = get_object_or_404(
            UserFavoriteBeer.objects.all(),
            user=user,
            beer=request.data["beer"],
        )
        instance.delete()
        return Response("", status=204)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateUserSerializer
        return super().get_serializer_class()

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (UserPermission,)
