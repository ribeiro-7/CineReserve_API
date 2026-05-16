from rest_framework import serializers

class BuySeatsSerializer(serializers.Serializer):
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

class TicketResponseSerializer(serializers.Serializer):
    seat = serializers.CharField()
    ticket_code = serializers.CharField()
    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    date = serializers.DateField()
    time = serializers.TimeField()

class BuySeatsResponseSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField()
    movie = serializers.CharField()
    tickets = TicketResponseSerializer(many=True)
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    payment_link = serializers.URLField()
    message = serializers.CharField()