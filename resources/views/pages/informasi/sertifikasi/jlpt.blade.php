@extends('layouts.master')
@section('content')

<!-- Header Start -->
<div class="container-fluid bg-breadcrumb">
    <div class="container text-center py-5" style="max-width: 900px;">
        <h3 class="text-white display-3 mb-4 wow fadeInDown" data-wow-delay="0.1s">Japanese Language Proficiency Test (JLPT)</h1>
        <ol class="breadcrumb justify-content-center text-white mb-0 wow fadeInDown" data-wow-delay="0.3s">
            <li class="breadcrumb-item"><a href="index.html" class="text-white">Home</a></li>
            <li class="breadcrumb-item"><a href="#" class="text-white">Informasi</a></li>
            <li class="breadcrumb-item"><a href="{{ route('informasi.sertifikasi') }}" class="text-white">Sertifikasi</a></li>
            <li class="breadcrumb-item active text-secondary">JLPT</li>
        </ol>    
    </div>
</div>
<!-- Header End -->

<!-- About Start -->
<div class="container-fluid overflow-hidden py-5">
  <div class="container legal-gallery">
    <div class="row">
        <div class="col-12 text-center mb-5">
            <h2 class="display-7">Informasi Sertifikasi JLPT</h2>
        </div>
    </div>
    <div class="row g-4">
        <div>
            <p class="has-text-align-left"><strong>JLPT</strong>&nbsp;adalah singkatan dari&nbsp;<em>Japanese Language Proficiency Test</em>&nbsp;atau dalam bahasa Jepangnya disebut 日本語能力試験 (nihongo nouryoku shiken). Ujian kemampuan bahasa Jepang yang ditujukan untuk orang-orang yang memiliki bahasa ibu bukan bahasa Jepang.</p>            
            <p class="has-text-align-left">JLPT pertama kali diselenggarakan pada Tahun 1984, dan diikuti oleh peserta dari 62 negara dengan jumlah sebanyak 600.000 orang.&nbsp;Ujian ini biasanya diselenggarakan 2 kali dalam setahun yaitu pada minggu pertama di bulan Juli dan bulan Desember.</p>
            <hr class="wp-block-separator">
                <h2 class="has-text-align-left wp-block-heading"><strong>Sesi Ujian JLPT</strong></h2>
                <p class="has-text-align-left"><strong>Adapun soal-soal yang di ujikan terdapat 4 sesi ujian yaitu :</strong><br><strong>文字語意&nbsp;(mojigoi)</strong>&nbsp;: menguji kemampuan peserta dalam memahami kosakata dalam bahasa Jepang dan kanji<br><strong>聴解&nbsp;(choukai)</strong>&nbsp;: menguji kemampuan peserta dalam mendengar dan memahami dialog dalam bahasa Jepang<br><strong>読解&nbsp;(dokkai)</strong>&nbsp;: menguji kemampuan peserta dalam memahami artikel dalam bahasa Jepang<br><strong>文法&nbsp;(bunpou)</strong>&nbsp;: menguji kemampuan peserta dalam memahami grammar bahasa Jepang</p>
                <p class="has-text-align-left">Sebelum tahun 2010, sistem penilaian JLPT adalah menjumlahkan nilai dari masing-masing bagian dan harus mencapai batas nilai tertentu.</p>
                <p class="has-text-align-left">Namun, Sejak tahun 2010 dan seterusnya, sistem penilaian ini diubah, setiap bagian memiliki standar nilai sendiri sehingga untuk lulus para peserta harus mampu mencapai nilai tertentu untuk masing-masing bagian (tidak berlaku sistem penilaian kumulatif seperti sebelumnya)</p>
            <hr class="wp-block-separator">
            <h2 class="has-text-align-left wp-block-heading"><strong>Level – Level yang terdapat di JLPT</strong></h2>
                <p class="has-text-align-left">Dalam tingkatan level kemampuan JLPT terdapat 5 level yaitu N1, N2, N3, N4 dan N5.</p>
                <p class="has-text-align-left">N5 adalah level terendah dan N1 adalah level tertinggi dan yang paling sulit, ini sebagai patokan untuk penentuan level JLPT. <br>Berikut penjalasan masing – masing level :</p>
            <h3 class="has-text-align-left wp-block-heading"><strong>1. Level N5</strong></h3>
                <p class="has-text-align-left">Menguasai Kanji sekitar : 100<br>Menguasai kosakata sekitar : 800<br>Dan bisa memahami kalimat standar jika ditulis dengan hiragana atau dengan kanji yang sangat sederhana.</p>
            <h3 class="has-text-align-left wp-block-heading"><strong>2. Level N4</strong></h3>
                <p class="has-text-align-left">Menguasai Kanji sekitar : 300<br>Menguasai kosakata sekitar : 1500<br>Dan dapat mengerti percakapan sehari-hari, jika diucapkan dengan lambat, dan dapat membaca materi sederhana</p>
            <h3 class="has-text-align-left wp-block-heading"><strong>3. Level N3</strong></h3>
                <p class="has-text-align-left">Menguasai Kanji sekitar : 650<br>Menguasai kosakata sekitar : 3750<br>Bisa mengerti artikel dalam bahasa Jepang jika ditulis dengan kanji-kanji yang mudah, dan dapat mengikuti perkataan orang Jepang dengan kecepatan normal.</p>
            <h3 class="has-text-align-left wp-block-heading"><strong>4. Level N2</strong></h3>
                <p class="has-text-align-left">Menguasai Kanji sekitar : 1000<br>Menguasai kosakata sekitar : 6000<br>Dan dapat memahami tulisan dengan topic umum dan mengerti percakapan dan berita dengan kecepatan normal</p>
            <h3 class="has-text-align-left wp-block-heading"><strong>5. Level N1</strong></h3>
                <p class="has-text-align-left">Menguasai Kanji sekitar : 2000<br>Menguasai kosakata sekitar : 10000<br>Dan dapat memahami berbagai macam percakapan dalam situasi tertentu. juga dapat memahami perbedaan nuansa dalam kalimat jika menggunakan kata tertentu.</p>
            <hr class="wp-block-separator">
            <h2 class="has-text-align-left wp-block-heading"><strong>Apa Manfaat Sertifikat JLPT?</strong></h2>
                <p class="has-text-align-left">Kegunaan sertifikat JLPT sesuai dengan levelnya yaitu sebagai berikut:<br>N1 : Bekerja di jepang dan perusahaan Jepang di Indoesia<br>N2 : Sebagai persyaratan Beasiswa atau melamar pekerjaan di Jepang<br>N3 : persyaratan melamar pekerjaan atau Magang di Jepang<br>N4-N5 : Masuk sekolah bahasa di Jepang</p>
            <hr class="wp-block-separator">
                <p class="has-text-align-left">Nah, khusus untuk pelaksanaan ujian tes JLPT yang berada di Indonesia, hanya terdapat dibeberapa lokasi atau kota saja. Berikut beberapa lokasi kota tempat dilaksanakannya Ujian JLPT. </p>
                <p><strong>Jadwal Ujian:</strong> <a href="https://jlptonline.or.id/lokasi-test/">https://jlptonline.or.id/lokasi-test/</a></p>
            <h2 class="has-text-align-left wp-block-heading">Daftar Lokasi Ujian &amp; Panitia Lokal</h2>
            <figure id="table-7676" class="wp-block-table is-style-stripes">
                <table>
                    <thead>
                        <tr>
                            <th scope="col">Kota</th>
                            <th scope="col">Institusi Penyelenggara</th>
                            <th class="has-text-align-left" data-align="left" scope="col">Juli</th>
                            <th scope="col">Desember</th>
                            <th scope="col">Telp / Fax / Email</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Jakarta</td>
                            <td><a href="https://jlptonline.or.id/assets/up/2019/11/3ae33521d75888bc33c22c68b94ac840.pdf">Sekretariat Persada/Universitas Darma Persada</a></td>
                            <td class="has-text-align-left" data-align="left">✔</td>
                            <td>✔</td>
                            <td>T：0813-1728-8205<br>F：-<br>M：jlpt.persada.jkt@gmail.com</td>
                        </tr>
                        <tr>
                            <td>Bandung</td>
                            <td><a href="http://fib.unpad.ac.id/jlpt-online">JLPT Administration Commitee in Bandung</a></td>
                            <td class="has-text-align-left" data-align="left">✔</td>
                            <td>✔</td>
                            <td>T：0877-8105-2467<br>F：022-7796388<br>M：jlptbandung@gmail.com</td>
                        </tr>
                        <tr>
                            <td>Semarang</td>
                            <td><a href="http://dinus.ac.id/">Committee of JLPT of Central Java</a></td>
                            <td class="has-text-align-left" data-align="left">✔</td>
                            <td>✖</td>
                            <td>T：0812-1500-0472 /<br>024-3564647<br>F：－<br>M：jlptjateng@gmail.com</td>
                        </tr>
                        <tr><td>Surabaya</td>
                            <td><a href="http://jepang.fbs.unesa.id/index.php/info-jlpt/jadwal-ujian/24-info-jlpt/jadwal-ujian/59-daftar-ruang-ujian-jlpt-juli-2019-test-site-surabaya">JLPT Administration Commitee in Surabaya</a></td>
                            <td class="has-text-align-left" data-align="left">✔</td>
                            <td>✔</td>
                            <td>T：0811-3444-200<br>F：-<br>M：bahasajepang@unesa.ac.id</td>
                        </tr>
                        <tr>
                            <td>Malang</td>
                            <td><a href="http://sastrajepang.fib.ub.ac.id/?page_id=2774">JLPT Administration Commitee in Malang</a></td>
                            <td class="has-text-align-left" data-align="left">✔</td>
                            <td>✔</td>
                            <td>T：0821-4076-8686<br>F：-<br>M：jlpt.malang@gmail.com</td>
                        </tr>
                        <tr>
                            <td>Medan</td>
                            <td><a href="http://sastrajepang.usu.ac.id/">JLPT Administration Commitee in Medan</a></td>
                            <td class="has-text-align-left" data-align="left">✔</td>
                            <td>✔</td>
                            <td>T：0812-6486-1346<br>F：-<br>M：jlpt.medan@gmail.com</td>
                        </tr>
                        <tr>
                            <td>Makassar</td>
                            <td><a href="http://www.unhas.ac.id/sastra/jepang/id/?p=JLPT-Makassar">Jurusan Sastra Jepang Fakultas Ilmu Budaya Universitas Hasanuddin</a></td>
                            <td class="has-text-align-left" data-align="left">✔</td>
                            <td>✖</td>
                            <td>T：0852-4252-9244<br>F：-<br>M：taqdir.unhas@gmail.com</td>
                        </tr>
                        <tr>
                            <td>Denpasar</td>
                            <td><a href="https://jlpt.unud.ac.id/?p=142">JLPT Administration Commitee in Denpasar</a></td>
                            <td class="has-text-align-left" data-align="left">✖</td>
                            <td>✔</td>
                            <td>T：0895-3349-07919<br>F：+62(3612)49458<br>M：jlpt.denpasar@gmail.com</td>
                        </tr>
                        <tr>
                            <td>Padang</td>
                            <td><a href="https://bunghatta.ac.id/jlpt-padang.html">JLPT Administration Commitee in Padang</a></td>
                            <td class="has-text-align-left" data-align="left">✔</td>
                            <td>✔</td>
                            <td>T：0813 7448 9411<br>F：<br>M：jlptpadang17@gmail.com</td>
                        </tr>
                        <tr>
                            <td>Yogyakarta</td>
                            <td><a href="http://sastrajepang.fib.ugm.ac.id/2019/11/05/ujian-kemampuan-bahasa-jepang-2019-wilayah-yogyakarta/">JLPT Administration Commitee in Yogyakarta</a></td>
                            <td class="has-text-align-left" data-align="left">✖</td>
                            <td>✔</td>
                            <td>T：+62 822-2012-5522<br>F：+62(274)550451<br>M：jlptjogja@gmail.com</td>
                        </tr>
                        <tr>
                            <td>Manado</td>
                            <td><a href="https://www.facebook.com/jlptmanado/?ref=bookmarks">Fakultas Ilmu Budaya, Universitas Sam Ratulangi (UNSRAT) Manado</a></td>
                            <td class="has-text-align-left" data-align="left">✖</td>
                            <td>✔</td>
                            <td>T：0812-1249-0004<br>0852-5659-4063<br>0812-1203-6623<br>0813-8044-4590<br>F：+62(431)869121<br>M：jlptmanado@yahoo.co.jp<br>panitianokenmanado@gmail.com</td>
                        </tr>
                        <tr>
                            <td>Palembang</td>
                            <td><a href="https://jlptonline.or.id/assets/up/2019/11/7c6f784764439e2f5c5239c3871756f7.png">JLPT Administration Commitee in Palembang</a></td>
                            <td class="has-text-align-left" data-align="left">✖</td>
                            <td>✔</td>
                            <td>T：0822 800 19748<br>0812 7319 7578 (WA)<br>M：santy_awe@yahoo.com</td>
                        </tr>
                    </tbody>
                </table>
            </figure>
                <p class="hs-text-align-left"><strong>Sumber:</strong>&nbsp;<em><a href="https://jlptonline.or.id/lokasi-test/">https://jlptonline.or.id/lokasi-test/</a></em>  atau di&nbsp;<a href="http://www.jlpt.jp/e/" rel="noreferrer noopener" target="_blank">http://www.jlpt.jp/e/</a></p>
        </div>
    </div>
</div>
</div>

@endsection