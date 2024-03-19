from django.http import HttpResponseServerError
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers, status
from rockapi.models import Rock, Type
from django.contrib.auth.models import User


class RockView(ViewSet):
    """Rock view set"""

    def create(self, request):
        """Handle POST operations

        Returns:
            Response -- JSON serialized instance
        """
        try:
            rock_type_instance = Type.objects.get(pk=request.data["typeId"])

            rock = Rock()
            rock.name = request.data["name"]
            rock.weight = request.data["weight"]
            rock.type = rock_type_instance
            rock.user = request.auth.user
            rock.save()

            serialized = RockSerializer(rock, many=False)

            return Response(serialized.data, status=status.HTTP_201_CREATED)

        except Exception as ex:
            return Response({"reason": ex.args[0]}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """Handle DELETE requests for a single item

        Returns:
            Response -- 200, 404, or 500 status code
        """
        try:
            rock = Rock.objects.get(pk=pk)
            if rock.user.id == request.auth.user.id:
                rock.delete()
                return Response(None, status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {"message": "You do not own that rock"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        except Rock.DoesNotExist as ex:
            return Response({"message": ex.args[0]}, status=status.HTTP_404_NOT_FOUND)

        except Exception as ex:
            return Response(
                {"message": ex.args[0]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def list(self, request):
        """Handle GET requests for all items

        Returns:
            Response -- JSON serialized array
        """

        owner_query_param = request.query_params.get("owner", None)

        try:
            rocks = Rock.objects.all()
            if owner_query_param is not None and owner_query_param == "current":
                rocks = rocks.filter(user=request.auth.user)

            serialized = RockSerializer(rocks, many=True)
            return Response(serialized.data, status=status.HTTP_200_OK)
        except Exception as ex:
            return HttpResponseServerError(ex)


class RockTypeSerializer(serializers.ModelSerializer):
    """JSON serializer for types
    Usage -- Will be used within RockSerializer to provide a nested type object within a rock JSON object
    """

    class Meta:
        model = Type
        fields = ("label",)


class RockUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
        )


class RockSerializer(serializers.ModelSerializer):
    """JSON serializer for rocks"""

    type = RockTypeSerializer(many=False)
    user = RockUserSerializer(many=False)

    class Meta:
        model = Rock
        fields = (
            "id",
            "name",
            "weight",
            "type",
            "user",
        )
