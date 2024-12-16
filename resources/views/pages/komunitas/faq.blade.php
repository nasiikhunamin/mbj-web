@extends('layouts.master')
@section('content')

<!-- Header Start -->
<div class="container-fluid bg-breadcrumb">
    <div class="container text-center py-5" style="max-width: 900px;">
        <h3 class="text-white display-3 mb-4 wow fadeInDown" data-wow-delay="0.1s">FAQ</h1>
        <ol class="breadcrumb justify-content-center text-white mb-0 wow fadeInDown" data-wow-delay="0.3s">
            <li class="breadcrumb-item"><a href="index.html" class="text-white">Home</a></li>
            <li class="breadcrumb-item"><a href="#" class="text-white">Komunitas</a></li>
            <li class="breadcrumb-item active text-secondary">FAQ</li>
        </ol>    
    </div>
</div>
<!-- Header End -->

<!-- About Start -->
<div class="container-fluid overflow-hidden py-5">
  <div class="container legal-gallery">
    <div class="row">
        <div class="col-12 text-center mb-5">
            <h2 class="display-7">Frequently Asked Question</h2>
            <p class="lead text-muted">Pertanyaan yang Sering Ditanyakan</p>
        </div>
    </div>
    <div class="row">
        <div class="accordion" id="faqAccordion">
            @php
            $faqs = [
                [
                    'id' => 'faq1',
                    'question' => 'Apa itu LPK Matahari Bulan Jepang Indonesia?',
                    'answer' => 'LPK Matahari Bulan Jepang Indonesia adalah lembaga pelatihan yang memberikan kesempatan bagi para calon peserta untuk mengikuti program magang di Jepang. Kami membantu peserta dalam proses seleksi, pelatihan bahasa Jepang, dan mempersiapkan semua dokumen untuk keberangkatan.'
                ],
                [
                    'id' => 'faq2',
                    'question' => 'Siapa yang bisa mendaftar untuk program magang ini?',
                    'answer' => 'Program magang ini terbuka bagi warga negara Indonesia yang memiliki usia 18 hingga 30 tahun, berpendidikan minimal SMA/SMK, dan memiliki niat untuk belajar dan bekerja di Jepang.'
                ],
                [
                    'id' => 'faq3',
                    'question' => 'Apa saja syarat untuk mengikuti program magang?',
                    'answer' => [
                        'Warga Negara Indonesia',
                        'Usia 18-30 tahun',
                        'Pendidikan minimal SMA/SMK',
                        'Sehat jasmani dan rohani',
                        'Mampu berkomunikasi dalam bahasa Indonesia dan dasar bahasa Jepang',
                        'Tidak memiliki riwayat kriminal'
                    ]
                ],
                [
                    'id' => 'faq4',
                    'question' => 'Bagaimana cara mendaftar ke LPK Matahari Bulan Jepang Indonesia?',
                    'answer' => 'Anda bisa mendaftar secara online melalui wa kami atau datang langsung ke kantor kami untuk mengisi formulir pendaftaran dan mengikuti tahapan seleksi yang sudah kami tentukan.'
                ],
                [
                    'id' => 'faq5',
                    'question' => 'Berapa lama waktu proses dari pendaftaran hingga keberangkatan?',
                    'answer' => 'Proses dari pendaftaran hingga keberangkatan biasanya memakan waktu sekitar 6-12 bulan, tergantung pada berbagai faktor seperti proses seleksi, pelatihan bahasa Jepang, dan pengurusan dokumen.'
                ],[
                    'id' => 'faq6',
                    'question' => 'Apakah peserta mendapatkan pelatihan bahasa Jepang?',
                    'answer' => 'Ya, peserta program magang di LPK Matahari Bulan Jepang Indonesia akan mendapatkan pelatihan bahasa Jepang dasar. Pelatihan ini bertujuan agar peserta dapat berkomunikasi dengan baik di Jepang dan memudahkan adaptasi di tempat magang.'
                ],[
                    'id' => 'faq7',
                    'question' => 'Apakah LPK Matahari Bulan Jepang Indonesia memberikan bantuan untuk pengurusan visa?',
                    'answer' => 'Ya, kami membantu peserta dalam proses pengajuan visa, termasuk pengurusan Certificate of Eligibility (CoE) dan paspor untuk keberangkatan ke Jepang.'
                ],[
                    'id' => 'faq8',
                    'question' => 'Berapa biaya yang dibutuhkan untuk mengikuti program magang?',
                    'answer' => 'Biaya program magang mencakup biaya pendaftaran, pelatihan bahasa Jepang, pemeriksaan medis, pengurusan visa, dan administrasi lainnya. Informasi lebih lengkap mengenai biaya dapat Anda lihat pada halaman biaya di website kami atau menghubungi customer service kami.'
                ],[
                    'id' => 'faq9',
                    'question' => 'Apakah saya akan ditempatkan di perusahaan tertentu di Jepang?',
                    'answer' => 'Setelah melewati proses seleksi dan wawancara, peserta akan ditempatkan di perusahaan di Jepang sesuai dengan keahlian dan bidang yang diinginkan. Kami bekerja sama dengan berbagai perusahaan di Jepang untuk memberikan peluang magang yang sesuai.'
                ],[
                    'id' => 'faq10',
                    'question' => 'Apakah saya akan mendapatkan gaji selama magang di Jepang?',
                    'answer' => 'Ya, peserta program magang akan menerima gaji selama periode magang di Jepang. Besarannya bervariasi tergantung pada perusahaan dan jenis pekerjaan yang dilakukan.'
                ],[
                    'id' => 'faq11',
                    'question' => 'Bagaimana jika saya memiliki masalah di Jepang selama magang?',
                    'answer' => 'Kami menyediakan dukungan penuh kepada peserta selama masa magang, baik dalam hal masalah pekerjaan maupun adaptasi di Jepang. Kami juga memiliki tim yang siap membantu peserta dalam mengatasi kesulitan yang mungkin timbul selama berada di Jepang.'
                ],[
                    'id' => 'faq12',
                    'question' => 'Apakah LPK Matahari Bulan Jepang Indonesia menyediakan tempat tinggal di Jepang?',
                    'answer' => 'Tempat tinggal selama magang di Jepang umumnya disediakan oleh perusahaan tempat peserta magang. Kami akan memberikan informasi terkait tempat tinggal yang disediakan perusahaan dan membantu dalam persiapan sebelum keberangkatan.'
                ],[
                    'id' => 'faq13',
                    'question' => 'Apa yang harus saya lakukan setelah selesai magang di Jepang?',
                    'answer' => 'Setelah selesai magang, peserta bisa memilih untuk kembali ke Indonesia atau melanjutkan program di Jepang, tergantung pada peraturan yang berlaku di Jepang dan kesepakatan dengan perusahaan tempat magang. Kami akan memberikan informasi terkait prosedur setelah program magang selesai.'
                ]
            ];
            @endphp

            @foreach($faqs as $index => $faq)
            <div class="accordion-item mb-2">
                <h2 class="accordion-header">
                    <button 
                        class="accordion-button {{ $index !== 0 ? 'collapsed' : '' }}" 
                        type="button" 
                        data-bs-toggle="collapse" 
                        data-bs-target="#{{ $faq['id'] }}"
                        aria-expanded="{{ $index === 0 ? 'true' : 'false' }}" 
                        aria-controls="{{ $faq['id'] }}"
                    >
                        {{ $faq['question'] }}
                    </button>
                </h2>
                <div 
                    id="{{ $faq['id'] }}" 
                    class="accordion-collapse collapse {{ $index === 0 ? 'show' : '' }}"
                    data-bs-parent="#faqAccordion"
                >
                <div class="accordion-body">
                    @if(is_array($faq['answer']))
                        <ul class="list-group list-group-flush">
                            @foreach($faq['answer'] as $item)
                                <li class="list-group-item">{{ $item }}</li>
                            @endforeach
                        </ul>
                    @else
                        {{ $faq['answer'] }}
                    @endif
                </div>
                </div>
            </div>
            @endforeach
        </div>
    </div>
</div>
</div>


<script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.6/dist/umd/popper.min.js"></script>


@endsection

