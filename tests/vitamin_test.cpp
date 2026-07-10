#include <set>
#include <string>
#include <utility>
#include <vector>

#include "cata_catch.h"
#include "type_id.h"
#include "vitamin.h"

static const vitamin_id vitamin_test_vit_extend_base( "test_vit_extend_base" );
static const vitamin_id vitamin_test_vit_extend_derived( "test_vit_extend_derived" );
static const vitamin_id vitamin_test_vit_excess_base( "test_vit_excess_base" );
static const vitamin_id vitamin_test_vit_excess_derived( "test_vit_excess_derived" );
static const vitamin_id vitamin_test_vit_empty_base( "test_vit_empty_base" );
static const vitamin_id vitamin_test_vit_empty_derived( "test_vit_empty_derived" );
static const vitamin_id vitamin_test_vit_delete_all_base( "test_vit_delete_all_base" );
static const vitamin_id vitamin_test_vit_delete_all_derived( "test_vit_delete_all_derived" );
static const vitamin_id vitamin_test_vit_override_and_extend( "test_vit_override_and_extend" );
static const vitamin_id vitamin_test_vit_chain_root( "test_vit_chain_root" );
static const vitamin_id vitamin_test_vit_chain_mid( "test_vit_chain_mid" );
static const vitamin_id vitamin_test_vit_chain_leaf( "test_vit_chain_leaf" );
static const vitamin_id vitamin_test_vit_override( "test_vit_override" );
static const vitamin_id vitamin_test_vit_flag_dedup( "test_vit_flag_dedup" );
static const vitamin_id vitamin_test_vit_decay_dup( "test_vit_decay_dup" );
static const vitamin_id vitamin_test_vitv( "test_vitv" );
static const vitamin_id vitamin_test_vitx( "test_vitx" );

TEST_CASE( "vitamin_copy_from_with_extend_and_delete", "[vitamin]" )
{
    REQUIRE( vitamin_test_vit_extend_base.is_valid() );
    REQUIRE( vitamin_test_vit_extend_derived.is_valid() );

    const vitamin &base = vitamin_test_vit_extend_base.obj();
    const vitamin &derived = vitamin_test_vit_extend_derived.obj();

    CHECK( base.name() == "Vitamin Extend Base" );
    CHECK( derived.name() == "Vitamin Extend Derived" );

    // Inherited scalar values should be copied from the base.
    CHECK( derived.min() == base.min() );
    CHECK( derived.max() == base.max() );
    CHECK( derived.rate() == base.rate() );

    // flags: base has TEST_FLAG_A; derived should also have TEST_FLAG_B.
    CHECK( base.has_flag( "TEST_FLAG_A" ) );
    CHECK_FALSE( base.has_flag( "TEST_FLAG_B" ) );
    CHECK( derived.has_flag( "TEST_FLAG_A" ) );
    CHECK( derived.has_flag( "TEST_FLAG_B" ) );

    // disease thresholds: base has two ranges; derived deletes the second and adds a third.
    CHECK( base.severity( -90 ) == 1 );
    CHECK( base.severity( -70 ) == 2 );
    CHECK( base.severity( -50 ) == 0 );

    CHECK( derived.severity( -90 ) == 1 );
    CHECK( derived.severity( -70 ) == 0 );
    CHECK( derived.severity( -50 ) == 2 );

    // decays_into: derived should keep the base entry and add the extended entry.
    const std::vector<std::pair<vitamin_id, int>> derived_decays = derived.decays_into();
    REQUIRE( derived_decays.size() == 2 );
    CHECK( derived_decays[0].first == vitamin_test_vitv );
    CHECK( derived_decays[0].second == 1 );
    CHECK( derived_decays[1].first == vitamin_test_vitx );
    CHECK( derived_decays[1].second == 2 );
}

TEST_CASE( "vitamin_disease_excess_extend_and_delete", "[vitamin]" )
{
    REQUIRE( vitamin_test_vit_excess_base.is_valid() );
    REQUIRE( vitamin_test_vit_excess_derived.is_valid() );

    const vitamin &base = vitamin_test_vit_excess_base.obj();
    const vitamin &derived = vitamin_test_vit_excess_derived.obj();

    // Base has two excess ranges.
    CHECK( base.severity( 15 ) == -1 );
    CHECK( base.severity( 25 ) == -2 );
    CHECK( base.severity( 35 ) == 0 );

    // Derived deletes [20,29] and extends [30,39].
    CHECK( derived.severity( 15 ) == -1 );
    CHECK( derived.severity( 25 ) == 0 );
    CHECK( derived.severity( 35 ) == -2 );
}

TEST_CASE( "vitamin_extend_empty_containers", "[vitamin]" )
{
    REQUIRE( vitamin_test_vit_empty_base.is_valid() );
    REQUIRE( vitamin_test_vit_empty_derived.is_valid() );

    const vitamin &derived = vitamin_test_vit_empty_derived.obj();

    CHECK( derived.has_flag( "TEST_FLAG_EMPTY" ) );
    CHECK( derived.severity( -45 ) == 1 );

    const std::vector<std::pair<vitamin_id, int>> derived_decays = derived.decays_into();
    REQUIRE( derived_decays.size() == 1 );
    CHECK( derived_decays[0].first == vitamin_test_vitv );
    CHECK( derived_decays[0].second == 3 );
}

TEST_CASE( "vitamin_delete_clears_entries", "[vitamin]" )
{
    REQUIRE( vitamin_test_vit_delete_all_base.is_valid() );
    REQUIRE( vitamin_test_vit_delete_all_derived.is_valid() );

    const vitamin &base = vitamin_test_vit_delete_all_base.obj();
    const vitamin &derived = vitamin_test_vit_delete_all_derived.obj();

    CHECK( base.has_flag( "TEST_FLAG_A" ) );
    CHECK( base.has_flag( "TEST_FLAG_B" ) );
    CHECK( base.severity( -90 ) == 1 );

    CHECK_FALSE( derived.has_flag( "TEST_FLAG_A" ) );
    CHECK_FALSE( derived.has_flag( "TEST_FLAG_B" ) );
    CHECK( derived.severity( -90 ) == 0 );
}

TEST_CASE( "vitamin_field_override_with_extend", "[vitamin]" )
{
    REQUIRE( vitamin_test_vit_override_and_extend.is_valid() );

    const vitamin &derived = vitamin_test_vit_override_and_extend.obj();

    CHECK( derived.max() == 200 );
    CHECK( derived.has_flag( "TEST_FLAG_C" ) );
    CHECK( derived.has_flag( "TEST_FLAG_D" ) );
}

TEST_CASE( "vitamin_copy_from_chain", "[vitamin]" )
{
    REQUIRE( vitamin_test_vit_chain_root.is_valid() );
    REQUIRE( vitamin_test_vit_chain_mid.is_valid() );
    REQUIRE( vitamin_test_vit_chain_leaf.is_valid() );

    const vitamin &leaf = vitamin_test_vit_chain_leaf.obj();
    const vitamin &root = vitamin_test_vit_chain_root.obj();

    CHECK( leaf.has_flag( "ROOT" ) );
    CHECK( leaf.has_flag( "MID" ) );
    CHECK( leaf.has_flag( "LEAF" ) );
    CHECK( leaf.min() == root.min() );
    CHECK( leaf.max() == root.max() );
    CHECK( leaf.rate() == root.rate() );
}

TEST_CASE( "vitamin_id_override", "[vitamin]" )
{
    REQUIRE( vitamin_test_vit_override.is_valid() );

    const vitamin &v = vitamin_test_vit_override.obj();

    CHECK( v.name() == "Override Replaced" );
    CHECK( v.min() == -200 );
    CHECK( v.max() == 200 );
}

TEST_CASE( "vitamin_flags_set_dedup", "[vitamin]" )
{
    REQUIRE( vitamin_test_vit_flag_dedup.is_valid() );

    const vitamin &derived = vitamin_test_vit_flag_dedup.obj();

    CHECK( derived.has_flag( "TEST_FLAG_A" ) );
}

TEST_CASE( "vitamin_decays_into_duplicate_entries", "[vitamin]" )
{
    REQUIRE( vitamin_test_vit_decay_dup.is_valid() );

    const vitamin &derived = vitamin_test_vit_decay_dup.obj();
    const std::vector<std::pair<vitamin_id, int>> derived_decays = derived.decays_into();

    REQUIRE( derived_decays.size() == 2 );
    CHECK( derived_decays[0].first == vitamin_test_vitv );
    CHECK( derived_decays[0].second == 1 );
    CHECK( derived_decays[1].first == vitamin_test_vitv );
    CHECK( derived_decays[1].second == 5 );
}
