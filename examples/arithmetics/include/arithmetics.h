
/**
\defgroup nmppsFFT256Fwd_f nmppsFFT256Fwd
\brief Функция инициализации структуры коэффициентов, необходимых для вычисления прямого БПФ-256
\param  x [in] входной вектор комплексных чисел (на мнимая и действительная части имеют тип float)
\retval X [out] выходной вектор комплексных чисел (на мнимая и действительная части имеют тип float)
\param spec [in] структра, содержащая необходимые коэффициенты, для вычисления прямого БПФ определенного размера
\par
\xmlonly
    <testperf>
		 <init>
		     NmppsFFTSpec_32fcr* spec;
		     nmppsFFT256FwdInitAlloc_32fcr(&amp;spec);
		 </init>
         <param name=" x "> im1 im2 im3 im4 im5 </param>
         <param name=" X "> im1 im2 im3 im4 im5 </param>
		 <size> 256 </size>
    </testperf>
\endxmlonly
*/
//! \{
void nmppsFFT256Fwd_32fcr(const nm32fcr* x, nm32fcr* X, NmppsFFTSpec_32fcr* spec);
//! \}

/**
\defgroup nmppsAdd_f nmppsAdd
\brief Сложение двух векторов.
\param pSrcVec1 [in] Первый входной вектор.
\param pSrcVec2 [in] Второй входной вектор.
\param nSize [in] Размер вектора в элементах.
\retval pDstVec [out] Результирующий вектор.
\par
\xmlonly
    <testperf>
         <param name=" pSrcVec1 "> im1 im2 </param>
         <param name=" pSrcVec2 "> im1 im2 </param>
         <param name=" pDstVec "> im2 </param>
         <param name=" nSize "> 2048 </param>
    </testperf>
    <testperf>
         <param name=" pSrcVec1 "> im1 </param>
         <param name=" pSrcVec2 "> im2 </param>
         <param name=" pDstVec "> im3 </param>
         <param name=" nSize "> 8 128 1024 2048 </param>
    </testperf>
\endxmlonly
*/
//! \{
void nmppsAdd_32f(const nm32f* pSrcVec1, const nm32f* pSrcVec2, nm32f* pDstVec, int nSize);
//! \}

/**
\defgroup nmppsMul_Add_f nmppsMul_Add
\brief Умножение с накоплением
\param pSrcVec1 [in] Входной вектор1
\param pSrcVec2 [in] Входной вектор2
\param pSrcVecAdd [in] Входной вектор
\param nSize [in] Размер векторов в элементах
\retval pDstVec [out] Результирующий вектор
\par
\xmlonly
	<testperf>
		 <param name=" pSrcVec1 "> im1 im2 </param>
		 <param name=" pSrcVec2 "> im2 im1 </param>
		 <param name=" pSrcVecAdd "> im3 </param>
		 <param name=" pDstVec "> im4 </param>
		 <param name=" nSize "> 2048*2 </param>
	</testperf>
	<testperf>
		<param name=" pSrcVec1 "> im1 </param>
		<param name=" pSrcVec2 "> im2 </param>
		<param name=" pSrcVecAdd "> im3 </param>
		<param name=" pDstVec "> im4 </param>
		<param name=" nSize "> 8 128 1024 2048 </param>
	</testperf>
\endxmlonly
*/
//! \{
void nmppsMul_Add_32f(const nm32f* pSrcVec1, const nm32f* pSrcVec2, const nm32f* pSrcVecAdd, nm32f* pDstVec, int nSize);
void nmppsMul_Add_64f(const nm64f* pSrcVec1, const nm64f* pSrcVec2, const nm64f* pSrcVecAdd, nm64f* pDstVec, int nSize);
//! \}

/**
\defgroup nmppsSub_f nmppsSub
\brief Вычитание двух вектров.
\param pSrcVec1 [in] Уменьшаемый вектор.
\param pSrcVec2 [in] Вычитаемый вектор.
\param nSize [in] Размер векторов в элементах.
\retval pDstVec [out] Результирующий вектор.
\par
\xmlonly
    <testperf>
         <param name=" pSrcVec1 "> im1 im2 </param>
         <param name=" pSrcVec2 "> im1 im2 </param>
         <param name=" pDstVec "> im1 im3 </param>
         <param name=" nSize "> 2048 </param>
    </testperf>
    <testperf>
         <param name=" pSrcVec1 "> im1 </param>
         <param name=" pSrcVec2 "> im2 </param>
         <param name=" pDstVec "> im3 </param>
         <param name=" nSize "> 8 128 1024 2048 </param>
    </testperf>
\endxmlonly
*/
//! \{
void nmppsSub_32f(const nm32f* pSrcVec1, const nm32f* pSrcVec2, nm32f* pDstVec, int nSize);
//! \}