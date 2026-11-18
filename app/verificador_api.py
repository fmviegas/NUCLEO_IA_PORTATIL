# -*- coding: utf-8 -*-
"""Nomes públicos de atributos/métodos de pandas, numpy, matplotlib e da biblioteca padrão,
gerados do dir() das bibliotecas (pandas 2.3.3, numpy 2.3.5, matplotlib 3.10.8).
O verificador nunca acusa df.<um destes> como "coluna com nome errado". Teste real 18/11:
ball_counts.values virou ball_counts.value porque o código tinha uma coluna 'value'."""

NOMES_DE_API = frozenset("""
AbstractContextManager Annotation Arrow ArrowDtype Artist ArtistList AutoLocator AxLine Axes BackendFilter
BitGenerator BooleanDtype Button Categorical CategoricalDtype CategoricalIndex Circle Colorizer
ColorizingArtist Colormap DataFrame DateOffset DatetimeIndex DatetimeTZDtype DirEntry EX_OK Enum ExcelFile
ExcelWriter ExecutableNotFoundError ExitStack F_OK False_ Figure FigureBase FigureCanvasBase FigureManagerBase
FixedFormatter FixedLocator Flags Float32Dtype Float64Dtype FormatStrFormatter Formatter FuncFormatter
Generator GenericAlias GridSpec Grouper HDFStore Index IndexLocator IndexSlice Int16Dtype Int32Dtype
Int64Dtype Int8Dtype Interval IntervalDtype IntervalIndex JSONDecodeError JSONDecoder JSONEncoder LinAlgError
Line2D LinearLocator Locator LogFormatter LogFormatterExponent LogFormatterMathtext LogLocator MT19937 Mapping
MatplotlibDeprecationWarning MaxNLocator MouseButton MultiIndex MultipleLocator MutableMapping NA NaT NamedAgg
Normalize NullFormatter NullLocator O_APPEND O_BINARY O_CREAT O_EXCL O_NOINHERIT O_RANDOM O_RDONLY O_RDWR
O_SEQUENTIAL O_SHORT_LIVED O_TEMPORARY O_TEXT O_TRUNC O_WRONLY PCG64 PCG64DXSM P_DETACH P_NOWAIT P_NOWAITO
P_OVERLAY P_WAIT Parameter Path PathLike Period PeriodDtype PeriodIndex Philox PolarAxes Polygon R_OK
RandomState RangeIndex RcParams Rectangle SEEK_CUR SEEK_END SEEK_SET SFC64 ScalarFormatter ScalarType
SeedSequence Series Slider SparseDtype StringDtype Subplot SubplotSpec T TMP_MAX TYPE_CHECKING Text TickHelper
Timedelta TimedeltaIndex Timestamp True_ UInt16Dtype UInt32Dtype UInt64Dtype UInt8Dtype W_OK Widget X_OK abc
abort abs absolute abspath access acorr acos acosh add add_artist add_axes add_axobserver add_callback
add_categories add_child_axes add_collection add_container add_dll_directory add_gridspec add_image add_line
add_patch add_prefix add_subfigure add_subplot add_suffix add_table addaudithook adjusted agg aggregate align
align_labels align_titles align_xlabels align_ylabels all allclose altsep amax amin anchor angle
angle_spectrum annotate annotations any api api_version append apply apply_along_axis apply_aspect
apply_over_axes applymap arange arccos arccosh arcsin arcsinh arctan arctan2 arctanh argmax argmin
argpartition argsort argv argwhere around array array2string array_equal array_equiv array_repr array_split
array_str arrays arrow artist artists as_integer_ratio as_ordered as_posix as_tuple as_unit as_unordered
as_uri asanyarray asarray asarray_chkfinite ascontiguousarray asfortranarray asfreq asi8 asin asinh asm8
asmatrix asof asof_locs assign astimezone astype at at_time atan atan2 atanh atexit atleast_1d atleast_2d
atleast_3d attrs audit autocorr autofmt_xdate autoscale autoscale_view autumn available_backends average axes
axhline axhspan axis axline axvline axvspan backend_bases backend_managers backend_registry backend_tools
backends backfill bar bar_label barbs barh bartlett base base_exec_prefix base_prefix base_repr basename
bdate_range beta between between_time bezier bfill binary_repr bincount binomial bit_count bit_generator
bit_length bitwise_and bitwise_count bitwise_invert bitwise_left_shift bitwise_not bitwise_or
bitwise_right_shift bitwise_xor bivar_colormaps blackman block bmat bone bool bool_ box boxplot breakpointhook
broadcast broadcast_arrays broadcast_shapes broadcast_to broken_barh builtin_module_names busday_count
busday_offset busdaycalendar bxp byte byteorder bytes bytes_ byteswap c_ call_tracing can_cast can_pan
can_zoom canonical capitalize case_when casefold cast cat categories category cbook cbrt cdouble ceil center
char character chdir check_for_ordered chisquare chmod choice cholesky choose cla clabel clear clf clim clip
clongdouble close closerange cm codecs codes cohere collections color_sequences colorbar colorizer colormaps
colors column_stack columns combine combine_first common_type commonpath commonprefix compare compare_signal
compare_total compare_total_mag compat complex128 complex64 complexfloating components compress concat
concatenate cond conj conjugate connect container contains contains_point contextlib contour contourf
convert_dtypes convert_xunits convert_yunits convolve cool copper copy copy_abs copy_negate copy_sign
copyright copysign copyto core corr corrcoef correlate corrwith cos cosh count count_nonzero cov cpu_count
cross crosstab csd csingle ctime ctypes ctypeslib cumcount cummax cummin cumprod cumsum cumulative_prod
cumulative_sum curdir cut cwd cycler data date date_range dates datetime64 datetime_as_string datetime_data
day day_name day_of_week day_of_year dayofweek dayofyear days days_in_month daysinmonth decode decoder
defaultParams default_factory default_rng defpath deg2rad degrees delaxes delete denominator describe
describe_option det detect_encoding device device_encoding devnull diag diag_indices diag_indices_from
diagflat diagonal diff difference difference_update digitize dirichlet dirname discard disconnect displayhook
div divide divmod dllhandle dont_write_bytecode dot double dpi drag_pan draw draw_all draw_artist
draw_if_interactive draw_without_rendering drive drop drop_duplicates droplevel dropna dsplit dst dstack dt
dtype dtypes dump dumps dup dup2 duplicated dviread e ecdf ediff1d eig eigh eigvals eigvalsh einsum
einsum_path elements emath empty empty_like encode encoder end end_pan end_time endpos endswith environ eq
equal equals error errorbar errors errstate euler_gamma eval eventplot ewm exc_info excepthook exception
exceptions exclusions exec_prefix execl execle execlp execlpe executable execv execve execvp execvpe exists
exit exp exp2 expand expand_dims expanding expandtabs expanduser expandvars explode expm1 exponential extend
extract extractall extsep eye f f2py fabs factorize fdopen ffill fft figaspect figimage figlegend
fignum_exists figtext figure fill fill_between fill_betweenx fill_diagonal fillna filter find findall finditer
findobj finfo first first_valid_index fix flag flags flat flatiter flatnonzero flatten flexible flip fliplr
flipud float16 float32 float64 float_info float_power float_repr_style floating floor floor_divide floordiv
fma fmax fmin fmod fold font_manager format format_coord format_cursor_data format_float_positional
format_float_scientific format_map format_xdata format_ydata frameon freq freqstr frexp from_bytes from_codes
from_dict from_dlpack from_dummies from_float from_records frombuffer fromfile fromfunction fromhex
fromisocalendar fromisoformat fromiter fromkeys fromordinal frompyfunc fromregex fromstring fromtimestamp
fsdecode fsencode fspath fstat fsync ft2font ftruncate full full_like fullmatch functools gamma gca gcd gcf
gci ge generic genericpath genfromtxt geometric geomspace get get_adjustable get_agg_filter get_alpha
get_anchor get_animated get_aspect get_asyncgen_hooks get_autoscale_on get_autoscalex_on get_autoscaley_on
get_axes get_axes_locator get_axisbelow get_backend get_bit_generator get_box_aspect get_cachedir get_children
get_clip_box get_clip_on get_clip_path get_cmap get_configdir get_constrained_layout
get_constrained_layout_pads get_coroutine_origin_tracking_depth get_current_fig_manager get_cursor_data
get_data_path get_data_ratio get_default_bbox_extra_artists get_dpi get_dummies get_edgecolor get_exec_path
get_facecolor get_fc get_figheight get_figlabels get_fignums get_figure get_figwidth
get_forward_navigation_events get_frame_on get_frameon get_gid get_gridspec get_group get_handle_inheritable
get_images get_in_layout get_include get_indexer get_indexer_for get_indexer_non_unique get_inheritable
get_int_max_str_digits get_label get_layout_engine get_legend get_legend_handles_labels get_level_values
get_lines get_linewidth get_loc get_mouseover get_navigate get_navigate_mode get_option get_path_effects
get_picker get_plot_commands get_position get_printoptions get_rasterization_zorder get_rasterized
get_scale_names get_shared_x_axes get_shared_y_axes get_size_inches get_sketch_params get_slice_bound get_snap
get_state get_subplotspec get_suptitle get_supxlabel get_supylabel get_terminal_size get_tight_layout
get_tightbbox get_title get_transform get_transformed_clip_path_and_affine get_url get_visible
get_window_extent get_xaxis get_xaxis_text1_transform get_xaxis_text2_transform get_xaxis_transform get_xbound
get_xgridlines get_xlabel get_xlim get_xmajorticklabels get_xmargin get_xminorticklabels get_xscale
get_xticklabels get_xticklines get_xticks get_yaxis get_yaxis_text1_transform get_yaxis_text2_transform
get_yaxis_transform get_ybound get_ygridlines get_ylabel get_ylim get_ymajorticklabels get_ymargin
get_yminorticklabels get_yscale get_yticklabels get_yticklines get_yticks get_zorder getallocatedblocks
getatime getbufsize getctime getcwd getcwdb getdefaultencoding getenv geterr geterrcall getfield
getfilesystemencodeerrors getfilesystemencoding getlogin getmtime getp getpid getppid getprofile
getrecursionlimit getrefcount getsize getsizeof getswitchinterval gettrace getwindowsversion ginput glob
gradient gray greater greater_equal grid gridspec group groupby groupdict grouper groupindex groups gt gumbel
half hamming hanning hardlink_to has_data has_duplicates hash_info hasnans hatch have_units head heaviside hex
hexbin hexversion hist hist2d histogram histogram2d histogram_bin_edges histogramdd hlines holds_integer home
hot hour hsplit hstack hsv hypergeometric hypot i0 iat identical identity idxmax idxmin iinfo iloc imag image
images implementation importlib imread imsave imshow in1d in_axes index index_exp indexer_at_time
indexer_between_time indicate_inset indicate_inset_zoom indices inexact inf infer_freq infer_objects inferno
inferred_freq inferred_type info inner insert inset inset_axes inspect install_repl_displayhook int16 int32
int64 int8 int_ int_info intc integer interactive intern interp interpolate intersect1d intersection
intersection_update interval_range intp inv invert invert_xaxis invert_yaxis io ioff ion is_ is_absolute
is_block_device is_boolean is_busday is_canonical is_categorical is_char_device is_dir is_fifo is_file
is_finalizing is_finite is_floating is_infinite is_integer is_interactive is_interval is_leap_year
is_monotonic_decreasing is_monotonic_increasing is_month_end is_month_start is_mount is_nan is_normal
is_normalized is_numeric is_object is_qnan is_quarter_end is_quarter_start is_relative_to is_reserved
is_signed is_snan is_socket is_subnormal is_symlink is_transform_set is_unique is_year_end is_year_start
is_zero isabs isalnum isalpha isascii isatty isclose iscomplex iscomplexobj isdecimal isdigit isdir isdisjoint
isdtype isetitem isfile isfinite isfortran isidentifier isin isinf isinteractive islink islower ismount isna
isnan isnat isneginf isnull isnumeric isocalendar isoformat isoweekday isposinf isprintable isreal isrealobj
isscalar isspace issubdtype issubset issuperset istitle isupper item items itemset itemsize iterable iterdir
iterrows itertuples ix_ jet join joinpath json_normalize kaiser keys kill kron kurt kurtosis label_outer
laplace last last_valid_index lastgroup lastindex layout_engine lchmod lcm ldexp le left_shift legend
legend_handler len less less_equal level lexists lexsort lib linalg lines linesep link link_to linspace list
listdir little_endian ljust ln load loads loadtxt loc locale locator_params log log10 log1p log2 logaddexp
logaddexp2 logb logging logical_and logical_invert logical_not logical_or logical_xor logistic loglog
lognormal logseries logspace long longdouble longlong lower lreshape lseek lstat lstrip lstsq lt mT ma magma
magnitude_spectrum makedirs maketrans map margins markers mask mask_indices match mathtext matmul matplotlib
matplotlib_fname matrix matrix_norm matrix_power matrix_rank matrix_transpose matshow matvec max max_mag
maximum maxsize maxunicode may_share_memory mean median melt memmap memory_usage merge merge_asof
merge_ordered meshgrid meta_path mgrid microsecond microseconds min min_mag min_scalar_type minimum
minorticks_off minorticks_on mintypecode minute mkdir mlab mod mode modf modules month month_name most_common
mouseover move_to_end moveaxis mtrand mul multi_dot multinomial multiply multivar_colormaps
multivariate_normal name namedtuple names nan nan_to_num nanargmax nanargmin nancumprod nancumsum nanmax
nanmean nanmedian nanmin nanosecond nanoseconds nanpercentile nanprod nanquantile nanstd nansum nanvar nbytes
ndarray ndenumerate ndim ndindex nditer ne nearest negative negative_binomial nested_iters new_figure_manager
newaxis newbyteorder next_minus next_plus next_toward nextafter ngroup ngroups nipy_spectral nlargest nlevels
noncentral_chisquare noncentral_f nonzero norm normal normalize normcase normpath not_equal notna notnull now
np nsmallest nth number number_class numerator nunique object_ offsetbox offsets ogrid ohlc ones ones_like
open option_context options ordered orig_argv os outer overload owner packbits pad pandas pardir parent
parents pareto parse_version partition parts patches path path_hooks path_importer_cache pathsep pattern pause
pchanged pcolor pcolorfast pcolormesh pct_change percentile period_range permutation permute_dims
phase_spectrum pi pick pickable pie piecewise pink pinv pipe pivot pivot_table place plasma platform
platlibdir plot plot_date plotting poisson polar poly poly1d polyadd polyder polydiv polyfit polyint polymul
polynomial polysub polyval pop popen popitem pos positive pow power pprint prefix printoptions prism prod
product projections promote_types properties psd ptp put put_along_axis putenv putmask pycache_prefix pyplot
qcut qr quantile quantize quarter query quiver quiverkey qyear r_ rad2deg radd radians radix rand randint
randn random random_integers random_sample ranf rank ravel ravel_multi_index rayleigh rc rcParams
rcParamsDefault rcParamsOrig rc_context rc_file rc_file_defaults rc_params rc_params_from_file rcdefaults
rcsetup rdiv rdivmod re read read_bytes read_clipboard read_csv read_excel read_feather read_fwf read_gbq
read_hdf read_html read_json read_orc read_parquet read_pickle read_sas read_spss read_sql read_sql_query
read_sql_table read_stata read_table read_text read_xml readlink real real_if_close realpath rec recarray
reciprocal record redraw_in_frame regs reindex reindex_like relative_to relim relpath remainder remainder_near
remove remove_callback remove_categories remove_unused_categories removedirs removeprefix removesuffix rename
rename_axis rename_categories renames reorder_categories reorder_levels repeat replace requested_backend
require resample reset_index reset_option reset_position reshape resize resolution resolution_string resolve
result_type reverse rfind rfloordiv rglob rgrids right_shift rindex rint rjust rmdir rmod rmul roll rollaxis
rolling root roots rot90 rotate round row_stack rpartition rpow rsplit rstrip rsub rtruediv s_ same_quantum
samefile sameopenfile samestat sample sanitize_sequence save savefig savetxt savez savez_compressed sca scale
scaleb scandir scanner scatter sci sctypeDict search searchsorted second secondary_xaxis secondary_yaxis
seconds seed select select_dtypes sem semilogx semilogy sep set set_adjustable set_agg_filter set_alpha
set_anchor set_animated set_aspect set_asyncgen_hooks set_autoscale_on set_autoscalex_on set_autoscaley_on
set_axes_locator set_axis set_axis_off set_axis_on set_axisbelow set_bit_generator set_box_aspect set_canvas
set_categories set_clip_box set_clip_on set_clip_path set_cmap set_constrained_layout
set_constrained_layout_pads set_coroutine_origin_tracking_depth set_dpi set_edgecolor set_eng_float_format
set_facecolor set_fc set_figheight set_figure set_figwidth set_flags set_forward_navigation_events
set_frame_on set_frameon set_gid set_handle_inheritable set_in_layout set_index set_inheritable
set_int_max_str_digits set_label set_layout_engine set_linewidth set_loglevel set_mouseover set_names
set_navigate set_navigate_mode set_option set_ordered set_path_effects set_picker set_position
set_printoptions set_prop_cycle set_rasterization_zorder set_rasterized set_size_inches set_sketch_params
set_snap set_state set_subplotspec set_tight_layout set_title set_transform set_url set_visible set_xbound
set_xlabel set_xlim set_xmargin set_xscale set_xticklabels set_xticks set_ybound set_ylabel set_ylim
set_ymargin set_yscale set_yticklabels set_yticks set_zorder setbufsize setdefault setdiff1d seterr seterrcall
setfield setflags setp setprofile setrecursionlimit setswitchinterval settrace setxor1d shape shares_memory
sharex sharey shift short show show_config show_runtime show_versions shuffle shutil sign signbit
signedinteger sin sinc single sinh size skew slice slice_indexer slice_locs slice_replace slogdet snap solve
sort sort_complex sort_index sort_values sortlevel spacing span sparse spawnl spawnle spawnv spawnve specgram
spines split splitdrive splitext splitlines spring spy sqrt square squeeze st stack stackplot stairs stale
standard_cauchy standard_exponential standard_gamma standard_normal standard_t start start_pan start_time
startfile startswith stat stat_result statvfs_result std stderr stdin stdlib_module_names stdout stem step
sticky_edges str str_ streamplot strerror strftime strides string strings strip strptime struct style sub
subfigures subn subplot subplot2grid subplot_mosaic subplot_tool subplots subplots_adjust subprocess subtract
suffix suffixes sum summer supports_bytes_environ supports_dir_fd supports_effective_ids supports_fd
supports_follow_symlinks supports_unicode_filenames suptitle supxlabel supylabel svd svdvals swapaxes swapcase
swaplevel switch_backend symlink symlink_to symmetric_difference symmetric_difference_update sys system table
tables tail take take_along_axis tan tanh tempfile tensordot tensorinv tensorsolve terminal_size test testing
texmanager text textpath texts thetagrids thread_info threading tick_params ticker ticklabel_format
tight_layout tile time timedelta64 timedelta_range times times_result timestamp timetuple timetz title
to_bytes to_clipboard to_csv to_datetime to_datetime64 to_device to_dict to_eng_string to_excel to_feather
to_flat_index to_frame to_gbq to_hdf to_html to_integral to_integral_exact to_integral_value to_json
to_julian_date to_latex to_list to_markdown to_numeric to_numpy to_orc to_parquet to_period to_pickle
to_pydatetime to_pytimedelta to_records to_series to_sql to_stata to_string to_timedelta to_timedelta64
to_timestamp to_xarray to_xml tobytes today tofile tolist toordinal total total_seconds touch trace transform
transforms translate transpose trapezoid trapz tri triangular tricontour tricontourf tril tril_indices
tril_indices_from trim_zeros tripcolor triplot triu triu_indices triu_indices_from true_divide truediv trunc
truncate tseries twinx twiny typecodes typename typing tz tz_convert tz_localize tzinfo tzname ubyte ufunc
uint uint16 uint32 uint64 uint8 uintc uintp ulong ulonglong umask uname_result uniform
uninstall_repl_displayhook union union1d unique unique_all unique_counts unique_inverse unique_values unit
units unlink unpackbits unraisablehook unravel_index unsetenv unsignedinteger unstack unwrap update
update_datalim update_from upper urandom use use_sticky_edges ushort utcfromtimestamp utcnow utcoffset
utctimetuple util utime validate_backend value value_counts values vander var vdot vecdot vecmat vector_norm
vectorize version version_info view viewLim violin violinplot viridis vlines void vonmises vsplit vstack
waitforbuttonpress waitpid waitstatus_to_exitcode wald walk warnoptions week weekday weekofyear weibull where
wide_to_long widgets winter winver with_name with_stem with_suffix wrap write write_bytes write_text
xaxis_date xaxis_inverted xcorr xkcd xlabel xlim xs xscale xticks yaxis_date yaxis_inverted year ylabel ylim
yscale yticks zeros zeros_like zfill zipf zorder
""".split())
