from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render, get_object_or_404
from tailored.models import UserProfile, Category, Section, Item, Review
from tailored.forms import Search_bar, ItemForm, EditUserProfileForm, UserProfileForm, ReviewForm, SoldItemForm
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from datetime import datetime, date
from django.contrib.auth.models import User
from django import forms
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from io import BytesIO
from PIL import Image
from os import path


@login_required
def delete(request, itemID):
	"""This view deletes the given item if the logged in user is the seller."""
	try:
		item = get_object_or_404(Item, itemID = itemID)

	# Handle when the given itemID is not a UUID
	except ValidationError:
		raise Http404

	if item.seller.user != request.user:
		raise Http404
	
	item.delete()
	return HttpResponseRedirect(reverse('tailored:index'))


def show_item(request, itemID):
	"""This view displays the given item and if the logged in user is the seller, it allows him to specify the
		buyer or delete the item."""
	try:
		item = get_object_or_404(Item, itemID = itemID)

	# Handle when the given itemID is not UUID
	except ValidationError:
		raise Http404

	context_dict = {}
	search_form = Search_bar()
	context_dict['search_bar'] = search_form
	context_dict['item'] = item
	context_dict['seller_rating'] = range(int(round(item.seller.rating, 1)))

	related = Item.objects.filter(category = item.category).exclude(itemID = item.itemID)
	
	if len(related) > 3:
		context_dict['trendingItems'] = related[0:3]
	else:
		context_dict['trendingItems'] = related

	response = render(request, 'tailored/product.html', context_dict)
	
	if first_visit(request, response, str(item.itemID)):
		item.dailyVisits += 1
		item.save()
		
	context_dict['itemID'] = item.itemID

	if item.seller.user != request.user:
		return response

	sold_form = SoldItemForm()

	if request.method == 'POST':
		sold_form = SoldItemForm(request.POST, request.FILES)

		if sold_form.is_valid():
			user_query = User.objects.filter(username = sold_form.cleaned_data['sold_to'])
			if not user_query:
				sold_form.add_error('sold_to', forms.ValidationError('The given user does not exist.'))
				context_dict['form'] = sold_form
				return render(request, 'tailored/product.html', context_dict)

			elif user_query[0] != request.user:
				try:
					item.sold_to = UserProfile.objects.get(user = user_query[0])
					item.save()
				except UserProfile.DoesNotExist:
					sold_form.add_error('sold_to', forms.ValidationError('The given user does not exist.'))
					context_dict['form'] = sold_form
					return render(request, 'tailored/product.html', context_dict)
			else:
				sold_form.add_error('sold_to', forms.ValidationError("You can't sell an item to yourself."))
				context_dict['form'] = sold_form
				return render(request, 'tailored/product.html', context_dict)
			item.save()
			return HttpResponseRedirect(reverse('tailored:index'))

	context_dict['form'] = sold_form
	return render(request, 'tailored/product.html', context_dict)
	


def trending(request):
	"""This view gives the five trending objects."""
	items = Item.objects.all()
	trending = []

	for item in Item.objects.order_by('-dailyVisits'):
		#Include items that have been uploaded within the past day and havent been sold
		if (date.today() - item.datePosted).days <= 0 and item.sold_to == None:
			if (len(trending) <= 5):
				trending.append(item)
		else:
			item.dailyVisits = 0
			item.save()

	#If there are not enough items in the trending list, add older items to the list
	if len(trending) <= 5:
		for item in Item.objects.order_by('-dailyVisits'):
			if ((len(trending) <= 5) and (item.sold_to == None) and (item not in trending)):
				trending.append(item)

	context_dict = {"trendingItems": trending[0:3], "search_bar" :Search_bar()}
	return render(request, 'tailored/index.html', context_dict)


def show_seller_profile(request, seller_username):
	"""This view shows the profile of the given seller."""
	context_dict = {}
	search_form = Search_bar()
	context_dict['search_bar'] = search_form

	seller_user = get_object_or_404(User, username = seller_username)
	context_dict['seller_user'] = seller_user
	
	seller_user_profile=get_object_or_404(UserProfile, user=seller_user)
	selling = Item.objects.filter(seller = seller_user_profile)
	context_dict['selling'] = selling[0:3]
	
	seller_user_profile = get_object_or_404(UserProfile, user = seller_user)
	context_dict['seller_user_profile'] = seller_user_profile
	context_dict['seller_rating'] = range(int(round(seller_user_profile.rating, 1)))

	seller_items = Item.objects.filter(seller = seller_user_profile)
	itemList = []

	for item in seller_items:
		if item.sold_to == None:
			itemList.append(item)

	context_dict['seller_items'] = itemList
	reviews_seller = Review.objects.filter(Q(item__in = Item.objects.filter(seller = seller_user_profile)))
	context_dict['reviews_seller'] = reviews_seller.order_by('-datePosted')

	if request.user.is_authenticated():
		items_reviewed = []
		for review in Review.objects.select_related():
			items_reviewed.append(review.item.itemID)
		
		items_to_review = Item.objects.filter(Q(sold_to__in = UserProfile.objects.filter( 
													user__in = User.objects.filter(username = request.user))) &
									Q(seller = seller_user_profile)
									).exclude(itemID__in = items_reviewed)
		context_dict['items_to_review'] = items_to_review

		if items_to_review:
			form = ReviewForm(user_items = items_to_review)
			if(request.method == 'POST'):
				form = ReviewForm(items_to_review, request.POST)
				if form.is_valid():
					review = form.save()
					# Remove item just reviewed from the items to review
					context_dict['items_to_review'] = items_to_review.exclude(itemID = review.item.itemID)

					# Handle if there are more items to review
					if context_dict['items_to_review']:
						context_dict['form'] = ReviewForm(user_items = context_dict['items_to_review'])

					reviews_seller_updated = Review.objects.filter(Q(item__in = Item.objects.filter(
																		seller = seller_user_profile)))
					rating = 0
					
					for review_updated in list(reviews_seller_updated):
						rating += review_updated.rating
					
					rating = round(rating/len(reviews_seller_updated), 1)
					seller_user_profile.rating = rating
					seller_user_profile.save()

					return HttpResponseRedirect(reverse('tailored:show_seller_profile',
							kwargs = {'seller_username': seller_username}))

			context_dict['form'] = form
	return render(request, 'tailored/seller_profile.html', context_dict)


@login_required
def user_profile(request):
	"""This view shows the profile of the authenticated user."""
	user = User.objects.get(username = request.user)
	user_profile = get_object_or_404(UserProfile, user = user)

	context_dict = {}
	search_form = Search_bar()
	context_dict['search_bar'] = search_form
	context_dict['user_profile'] = user_profile
	context_dict['user_rating'] = range(int(round(user_profile.rating, 0)))
	
	reviews_user = Review.objects.filter(Q(item__in = Item.objects.filter(seller = user_profile)))
	context_dict['reviews_user'] = reviews_user.order_by('-datePosted')

	user_items = Item.objects.filter(seller = user_profile, sold_to = None)
	context_dict['user_items'] = user_items
	
	item_form = ItemForm()
	user_form = EditUserProfileForm()

	if request.method == "POST":
		item_form = ItemForm(request.POST, request.FILES)
		user_form = EditUserProfileForm(request.POST, request.FILES)
		
		if item_form.is_valid():
			item = item_form.save(commit = False)

			if not item_form.cleaned_data['picture']:
				# Handle when the user does not upload an image for the item
				image = Image.open(path.dirname(path.dirname(path.abspath(__file__))) + static('images/item.png'))
				output = BytesIO()
				image.save(output, 'PNG', quality = 100)
				output.seek(0)
				
				file_system = FileSystemStorage(settings.MEDIA_ROOT + '/item_images/')
				filename = file_system.save('item.png', output)
				file_url = file_system.url(filename)

				item.picture = file_url.replace('/media', 'item_images', 1)
			else:
				item.picture = item_form.cleaned_data['picture']

			item.seller = user_profile
			item.save()

			context_dict['user_form'] = user_form
			return HttpResponseRedirect(reverse('tailored:index'))

		elif user_form.is_valid():
			if user_form.has_changed():
				user_form_keys = list(user_form.cleaned_data.keys())
				
				for key in user_form_keys[:2]:
					if user_form.cleaned_data[key] and user.__dict__[key] != user_form.cleaned_data[key]:
						user.__dict__[key] = user_form.cleaned_data[key]
				user.save()

				for key in user_form_keys[2:]:
					if user_form.cleaned_data[key] and user_profile.__dict__[key] != user_form.cleaned_data[key]:
						user_profile.__dict__[key] = user_form.cleaned_data[key]
				user_profile.save()

				context_dict['item_form'] = item_form
				return HttpResponseRedirect(reverse('tailored:index'))
			else:
				keys = list(user_form.cleaned_data.keys())
				
				for key in keys:
					user_form.add_error(key, forms.ValidationError("You need to fill at least one field."))
				
				context_dict['item_form'] = item_form
				context_dict['user_form'] = user_form
				return render(request, 'tailored/user_profile.html', context_dict)

	context_dict['item_form'] = item_form
	context_dict['user_form'] = user_form
	return render(request, "tailored/user_profile.html", context_dict)


def search_bar(request, search = None):
	"""This view takes care of searching objects."""
	categories = Category.objects.all()

	if request.method == 'POST':
		search_form = Search_bar(request.POST)
		if search_form.is_valid():
			if search_form.cleaned_data['search']:
				parameters = '-'.join(search_form.cleaned_data['search'].split(' '))
				return HttpResponseRedirect(reverse('tailored:search', kwargs = {'search': parameters}))
			else:
				return HttpResponseRedirect('all/')

	context_dict = {}
	form = Search_bar()
	context_dict['search_bar'] = form
	context_dict['categories'] = categories
	items = []

	if search == 'all' or search == None or search == '':
		search = 'all'
		items = Item.objects.filter(sold_to = None)
	else:
		if search != None:
			search = search.split('-')
			for word in search:
				items += Item.objects.filter((Q(description__contains = word ) | Q(title__contains = word)
					| Q(category = word) | Q(section = word)) & Q(sold_to = None))
			searchS = '_'.join(search)
			context_dict['search'] = searchS
		else:
			return home_page(request)
	
	maxi = 0
	
	for item in items:
		if item.price > maxi:
			maxi = item.price
	
	context_dict['maxi'] = maxi + 5
	context_dict['items'] = items
	context_dict['pages'] = int(len(items)/6)
	
	return render(request, 'tailored/shop_bootstrap.html',context_dict)


def new_in(request, search = None, page = 1):
	"""This view shows the new items in the website."""
	context_dict = {}
	items = []	
	search = search

	if search != None:
		search = search.split(" ")
		toAdd = []
		
		for word in search:
			toAdd += Item.objects.filter(Q(description__contains = word ) | Q(title__contains = word)
				| Q(category = word) | Q(section = word))
			
			for item in toAdd:
				if (date.today()- item.datePosted).days <= 7:
					items += [item]
		
		searchS = "_".join(search)
		maxi = 0
		
		for item in items:
			if item.price > maxi:
				maxi = item.price
		
		serch_form = Search_bar()
		context_dict['search_bar'] = search_form
		context_dict['maxi'] = maxi + 5
		context_dict['search'] = searchS
		context_dict['page']  = page
		context_dict['items'] = items
		context_dict['pages'] = int(len(items)/6)
		context_dict['min'] = 6 * (int(page) - 1)
		context_dict['max'] = 6 * (int(page))
		
		return render(request, 'tailored/shop_bootstrap.html',context_dict)
	else:
		return home_page(request)


def terms_and_conditions(request):
	"""This view shows the terms and conditions of the website."""
	return render(request, 'tailored/terms_and_conditions.html', {})


def first_visit(request, response, item):
	"""This function checks if the given request is the first visit from that computer to the given item."""
	if request.user == item.seller.user:
		return False

	last_visit_cookie = request.COOKIES.get('last_visit' + item, "first")
	
	if last_visit_cookie == "first":
		response.set_cookie('last_visit' + item, str(datetime.now()))
		return True
	else:
		last_visit_time = datetime.strptime(last_visit_cookie[:-7], '%Y-%m-%d %H:%M:%S')
		if (datetime.now() - last_visit_time).days > 0:
			response.set_cookie('last_visit' + item, str(datetime.now()))
			return True
		else:
			response.set_cookie('last_visit' + item , last_visit_cookie)
			return False