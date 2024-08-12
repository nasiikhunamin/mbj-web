@extends('layouts.master')
@section('content')

<!-- Header Start -->
<div class="container-fluid bg-breadcrumb">
    <div class="container text-center py-5" style="max-width: 900px;">
        <h3 class="text-white display-3 mb-4 wow fadeInDown" data-wow-delay="0.1s">Struktur Organisasi</h1>
        <ol class="breadcrumb justify-content-center text-white mb-0 wow fadeInDown" data-wow-delay="0.3s">
            <li class="breadcrumb-item"><a href="index.html" class="text-white">Home</a></li>
            <li class="breadcrumb-item"><a href="#" class="text-white">Profile</a></li>
            <li class="breadcrumb-item active text-secondary">Struktur Organisasi</li>
        </ol>    
    </div>
</div>
<!-- Header End -->

<!-- About Start -->
<div class="container-fluid overflow-hidden py-5">
    <div class="container">
        <div class="row g-4">
            <div class="col-lg-6 col-md-6 wow fadeInUp d-flex justify-content-center" data-wow-delay="0.1s">
                <div class="team-item position-relative rounded overflow-hidden">
                    <div class="overflow-hidden d-flex justify-content-center">
                        <img class="img-fluid" src="{{ asset('asset/img/team-1.jpg') }}" alt="">
                    </div>
                    <div class="team-text bg-light text-center p-4">
                        <h5>Full Name</h5>
                        <p class="text-primary">Designation</p>
                    </div>
                </div>
            </div>
            <div class="col-lg-6 col-md-6 wow fadeInUp d-flex justify-content-center" data-wow-delay="0.3s">
                <div class="team-item position-relative rounded overflow-hidden">
                    <div class="overflow-hidden d-flex justify-content-center">
                        <img class="img-fluid" src="{{ asset('asset/img/team-2.jpg') }}" alt="">
                    </div>
                    <div class="team-text bg-light text-center p-4">
                        <h5>Full Name</h5>
                        <p class="text-primary">Designation</p>
                    </div>
                </div>
            </div>
        </div>
        <div class="row g-4 py-5">
            <div class="col-lg-3 col-md-6 wow fadeInUp d-flex justify-content-center" data-wow-delay="0.5s">
                <div class="team-item position-relative rounded overflow-hidden">
                    <div class="overflow-hidden d-flex justify-content-center">
                        <img class="img-fluid" src="{{ asset('asset/img/team-3.jpg') }}" alt="">
                    </div>
                    <div class="team-text bg-light text-center p-4">
                        <h5>Full Name</h5>
                        <p class="text-primary">Designation</p>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6 wow fadeInUp d-flex justify-content-center" data-wow-delay="0.7s">
                <div class="team-item position-relative rounded overflow-hidden">
                    <div class="overflow-hidden d-flex justify-content-center">
                        <img class="img-fluid" src="{{ asset('asset/img/team-4.jpg') }}" alt="">
                    </div>
                    <div class="team-text bg-light text-center p-4">
                        <h5>Full Name</h5>
                        <p class="text-primary">Designation</p>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6 wow fadeInUp d-flex justify-content-center" data-wow-delay="0.5s">
                <div class="team-item position-relative rounded overflow-hidden">
                    <div class="overflow-hidden d-flex justify-content-center">
                        <img class="img-fluid" src="{{ asset('asset/img/team-3.jpg') }}" alt="">
                    </div>
                    <div class="team-text bg-light text-center p-4">
                        <h5>Full Name</h5>
                        <p class="text-primary">Designation</p>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6 wow fadeInUp d-flex justify-content-center" data-wow-delay="0.7s">
                <div class="team-item position-relative rounded overflow-hidden">
                    <div class="overflow-hidden d-flex justify-content-center">
                        <img class="img-fluid" src="{{ asset('asset/img/team-4.jpg') }}" alt="">
                    </div>
                    <div class="team-text bg-light text-center p-4">
                        <h5>Full Name</h5>
                        <p class="text-primary">Designation</p>
                    </div>
                </div>
            </div>
        </div>
        <div class="row g-4 py-5">
            <div class="col-lg-3 col-md-6 wow fadeInUp d-flex justify-content-center" data-wow-delay="0.5s">
                <div class="team-item position-relative rounded overflow-hidden">
                    <div class="overflow-hidden d-flex justify-content-center">
                        <img class="img-fluid" src="{{ asset('asset/img/team-3.jpg') }}" alt="">
                    </div>
                    <div class="team-text bg-light text-center p-4">
                        <h5>Full Name</h5>
                        <p class="text-primary">Designation</p>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6 wow fadeInUp d-flex justify-content-center" data-wow-delay="0.7s">
                <div class="team-item position-relative rounded overflow-hidden">
                    <div class="overflow-hidden d-flex justify-content-center">
                        <img class="img-fluid" src="{{ asset('asset/img/team-4.jpg') }}" alt="">
                    </div>
                    <div class="team-text bg-light text-center p-4">
                        <h5>Full Name</h5>
                        <p class="text-primary">Designation</p>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6 wow fadeInUp d-flex justify-content-center" data-wow-delay="0.5s">
                <div class="team-item position-relative rounded overflow-hidden">
                    <div class="overflow-hidden d-flex justify-content-center">
                        <img class="img-fluid" src="{{ asset('asset/img/team-3.jpg') }}" alt="">
                    </div>
                    <div class="team-text bg-light text-center p-4">
                        <h5>Full Name</h5>
                        <p class="text-primary">Designation</p>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6 wow fadeInUp d-flex justify-content-center" data-wow-delay="0.7s">
                <div class="team-item position-relative rounded overflow-hidden">
                    <div class="overflow-hidden d-flex justify-content-center">
                        <img class="img-fluid" src="{{ asset('asset/img/team-4.jpg') }}" alt="">
                    </div>
                    <div class="team-text bg-light text-center p-4">
                        <h5>Full Name</h5>
                        <p class="text-primary">Designation</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>


    

<!-- About End -->

@endsection

