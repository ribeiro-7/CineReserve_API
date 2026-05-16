from rest_framework import serializers

class ReserveSeatsSerializer(serializers.Serializer):
    seat_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )

    def validate_seat_ids(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                "Duplicated seat ids are not allowed."
            )
        return value
    
class ReservedSeatSerializer(serializers.Serializer):
    seat = serializers.CharField()
    status = serializers.CharField()
    expires_at = serializers.CharField()

class ReserveSeatsResponseSerializer(serializers.Serializer):
    reserved_seats = ReservedSeatSerializer(many=True)