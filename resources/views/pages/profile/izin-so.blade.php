@extends('layouts.master')
@section('content')

<!-- Header Start -->
<div class="container-fluid bg-breadcrumb">
    <div class="container text-center py-5" style="max-width: 900px;">
        <h3 class="text-white display-3 mb-4 wow fadeInDown" data-wow-delay="0.1s">Izin SO</h1>
        <ol class="breadcrumb justify-content-center text-white mb-0 wow fadeInDown" data-wow-delay="0.3s">
            <li class="breadcrumb-item"><a href="index.html" class="text-white">Home</a></li>
            <li class="breadcrumb-item"><a href="#" class="text-white">Profile</a></li>
            <li class="breadcrumb-item active text-secondary">Izin SO</li>
        </ol>    
    </div>
</div>
<!-- Header End -->

<!-- About Start -->
<div class="container-fluid overflow-hidden py-5">
    <div class="container">
        <div class="row h_blog_item">
          <div class="col-lg-6">
            <div class="h_blog_img">
              <img class="img-fluid" src="{{ asset('asset/img/about.png') }}" alt="">
            </div>
          </div>
          <div class="col-lg-6">
            <div class="h_blog_text">
              <div class="h_blog_text_inner left right">
                <h4>Welcome to our Institute</h4>
                <p>
                  Subdue whales void god which living don't midst lesser
                  yielding over lights whose. Cattle greater brought sixth fly
                  den dry good tree isn't seed stars were.
                </p>
                <p>
                  Subdue whales void god which living don't midst lesser yieldi
                  over lights whose. Cattle greater brought sixth fly den dry
                  good tree isn't seed stars were the boring.
                </p>
              </div>
            </div>
          </div>
        </div>
    </div>
</div>
    

<!-- About End -->

@endsection

