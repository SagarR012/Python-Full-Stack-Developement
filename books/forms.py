from django import forms
from .models import Book,Review


class BookForm(forms.ModelForm):
    class Meta:
        model =Book
        fields = ['title','author','cover','description']
            

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating','comment']


        def clean_rating(self):
            rating = self.cleaned_data.get('rating')
            if rating < 1 or rating > 5 :
                raise forms.ValidationError('rating must be between 1 and 5')
            return rating